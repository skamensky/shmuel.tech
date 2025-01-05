package traktv

import (
	"fmt"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/input"
	"github.com/go-rod/rod/lib/launcher"
	"github.com/hashicorp/go-retryablehttp"
	"github.com/skamensky/skam.dev/internal/db"
	"github.com/skamensky/skam.dev/internal/media/common"
	"gorm.io/gorm"
	"log"
	"net/http"
	"strings"
	"sync"
)

var TRAKT_BASE_URL = "https://api.trakt.tv"
var TMDB_BASE_URL = "https://api.themoviedb.org/3"

type TraktItemList struct {
	db            *gorm.DB
	httpClient    *retryablehttp.Client
	authInfo      *db.MediaAuth
	tmdbAuthInfo  *db.MediaAuth
	WatchedMovies []*WatchedMovie
	ToWatchMovies []*ToWatchMovie
	WatchedShows  []*WatchedShow
}

func (list *TraktItemList) GetAllAsMediaItems() []d
+b.MediaItem {
	retVal := make([]common.MediaItem, len(list.WatchedShows)+len(list.WatchedMovies)+len(list.ToWatchMovies))
	for _, movie := range list.WatchedMovies {
		retVal = append(retVal, &movie.Movie)
	}
	for _, movie := range list.ToWatchMovies {
		retVal = append(retVal, &movie.Movie)
	}
	for _, show := range list.WatchedShows {
		retVal = append(retVal, &show.Show)
	}
	return retVal
}

func (list *TraktItemList) setAccessToken() error {
	res := list.db.Where("service_name = ?", "trakt").First(&list.authInfo)
	if res.Error != nil {
		return res.Error
	}

	expired := false
	if list.authInfo.Token == "" {
		expired = true
	} else {
		tokenExpiredRes, err := tokenExpired(list.httpClient, list.authInfo)
		if err != nil {
			return err
		}
		expired = tokenExpiredRes
	}

	if expired {
		codeReq := prepareTraktReq(
			"POST",
			"/oauth/device/code",
			map[string]string{
				"client_id": list.authInfo.APIKey,
			},
			list.authInfo,
		)

		devCodeResp := &traktDeviceCodeResponse{}
		err := doReqAndMarshal(codeReq, list.httpClient, devCodeResp)
		if err != nil {
			return err
		}
		err = list.authorizeUsingBrowser(devCodeResp)
		if err != nil {
			return err
		}
		tokenReq := prepareTraktReq(
			"POST",
			"/oauth/device/token",
			map[string]string{
				"code":          devCodeResp.DeviceCode,
				"client_id":     list.authInfo.APIKey,
				"client_secret": list.authInfo.APISecret,
			},
			list.authInfo,
		)
		tokenResp := &traktTokenResponse{}
		err = doReqAndMarshal(tokenReq, list.httpClient, tokenResp)
		if err != nil {
			return err
		}
		list.authInfo.Token = tokenResp.AccessToken
		saveRes := list.db.Save(&list.authInfo)
		if saveRes.Error != nil {
			return saveRes.Error
		}
	}

	return nil
}

func (list *TraktItemList) PersistToDB() error {
	// TODO
	list.db.Delete(&db.MediaItem{}, "service_name = ?", "trakt")
	list.db.Create(list.GetAllAsMediaItems())
	return nil
}

func (list *TraktItemList) RetrieveItemsFromDB() ([]common.MediaItem, error) {
	// TODO
	return list.GetAllAsMediaItems(), nil
}

func (list *TraktItemList) RetrieveItemsFromTracker() ([]common.MediaItem, error) {
	log.Println("Getting watched movies")
	watchedMoviesReq := prepareTraktReq(
		"GET",
		"/sync/watched/movies",
		nil,
		list.authInfo,
	)
	watchedMovies := []*TraktWatchedMovie{}
	err := doReqAndMarshal(watchedMoviesReq, list.httpClient, &watchedMovies)
	if err != nil {
		return nil, err
	}

	log.Println("Getting watched shows")
	watchedShowsReq := prepareTraktReq(
		"GET",
		"/sync/watched/shows",
		nil,
		list.authInfo,
	)
	watchedShows := []*TraktWatchedShow{}
	err = doReqAndMarshal(watchedShowsReq, list.httpClient, &watchedShows)
	if err != nil {
		return nil, err
	}

	log.Println("Getting movies on watchlist")
	toWatchMovies := []*TraktToWatchMovie{}
	toWatchMoviesReq := prepareTraktReq("GET", "/sync/watchlist/movies/added", nil, list.authInfo)
	err = doReqAndMarshal(toWatchMoviesReq, list.httpClient, &toWatchMovies)
	if err != nil {
		return nil, err
	}

	err = list.enrichWithTmdb(watchedMovies, watchedShows, toWatchMovies)
	if err != nil {
		return nil, err
	}
	return list.GetAllAsMediaItems(), nil
}

func (list *TraktItemList) RetrievePrivateIdsFromDB() []string {
	return nil
}

func (list *TraktItemList) Init(db *gorm.DB) error {

	list.db = db
	list.httpClient = retryablehttp.NewClient()
	// this is a static api token, no auth required
	res := list.db.Where("service_name = ?", "tmdb").First(&list.tmdbAuthInfo)
	if res.Error != nil {
		return res.Error
	}
	return list.setAccessToken()

}

func tokenExpired(httpClient *retryablehttp.Client, authInfo *db.MediaAuth) (bool, error) {
	// todo, use the expired at data provided from the response to check this before doing a request
	//  the reason I'm not doing that now is because the db table storing auth data is generic
	//	 and doesn't have a column for traktv specific data

	/*
		expiresAt := time.Unix(int64(t.CreatedAt), 0).Add(time.Duration(t.ExpiresIn) * time.Second).In(time.UTC)
		// give ourselves a 10 minutes leeway so we don't run into an expired token while processing
		in10Minutes := time.Now().In(time.UTC).Add(10 * time.Minute)
		// pessimistic check
		officiallyExpired := expiresAt.Before(in10Minutes)
		if officiallyExpired {
			return true, nil
		}
	*/

	req := prepareTraktReq("GET", "/users/settings", nil, authInfo)
	resp, err := httpClient.Do(req)
	if err != nil {
		return false, err
	}
	actuallyExpired := resp.StatusCode != 200
	return actuallyExpired, nil
}

func (list *TraktItemList) authorizeUsingBrowser(devCodeResp *traktDeviceCodeResponse) (err error) {
	defer func() {
		// sorry, but this is just much nicer than checking 23 errors
		if r := recover(); r != nil {
			err = fmt.Errorf("error while doing browser authorization: %v", r)
		}
	}()
	lncher := launcher.MustNewManaged("")
	log.Println("Connecting to remote browser")
	//u := launcher.MustResolveURL("")
	browser := rod.New().Client(lncher.MustClient()).MustConnect()
	//browser := rod.New().ControlURL(u).MustConnect().MustIncognito()
	// for debugging:
	//launcher.Open(browser.ServeMonitor(""))
	log.Println("Loading trakt.tv signin page")

	pg := browser.MustPage("https://trakt.tv/auth/signin")

	log.Println("Waiting for login form to load")
	pg.MustWaitLoad()
	pg.MustWaitElementsMoreThan("input[name='user[login]']", 0)
	log.Println("Page loaded. Attempting to log in.")
	pg.MustElement("input[name='user[login]']").MustInput(list.authInfo.Username)
	pg.MustElement("input[name='user[password]']").MustInput(list.authInfo.Password).MustType(input.Enter)
	log.Println("Waiting for login to redirect")
	pg.MustWaitElementsMoreThan("a[href='/logout']", 0)
	log.Println("Logged in. Navigating to device code page")
	pg.MustNavigate(devCodeResp.VerificationURL)
	log.Println("Waiting for device code to load")
	pg.MustWaitLoad()
	log.Println("Device code loaded. Attempting to enter device code")
	pg.MustWaitElementsMoreThan("input[id='code']", 0)
	log.Println("Entered device code, waiting for confirmation screen")
	pg.MustElement("input[id='code']").MustInput(devCodeResp.UserCode).MustType(input.Enter)
	pg.MustWaitElementsMoreThan("input[value=Yes]", 0)
	log.Println("Confirming...")
	pg.MustElement("input[value=Yes]").MustClick()
	pg.MustWaitElementsMoreThan("div.approved", 0)
	log.Println("Confirmed!")
	browser.MustClose()

	return
}

func (list *TraktItemList) getMovieData(tmdbId int, movieChan chan<- *TmdbMovie, errorChan chan<- error) {
	movieReq := prepareTmdbReq(fmt.Sprintf("/movie/%v", tmdbId), list.tmdbAuthInfo)
	movie := &TmdbMovie{}
	err := doReqAndMarshal(movieReq, list.httpClient, movie)
	if err != nil {
		errorChan <- err
	} else {
		movieChan <- movie
	}

}

func (list *TraktItemList) getShowData(tmdbId int, showChan chan<- *TmdbShow, errorChan chan<- error) {
	showReq := prepareTmdbReq(fmt.Sprintf("/tv/%v", tmdbId), list.tmdbAuthInfo)
	show := &TmdbShow{}
	err := doReqAndMarshal(showReq, list.httpClient, show)
	if err != nil {
		errorChan <- err
	} else {
		showChan <- show
	}

}

func (entry *TraktEntry) GetThumbnail(httpClient *http.Client, url string, key string) error {
	resp, err := httpClient.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	return err
}

func (list *TraktItemList) enrichWithTmdb(watchedMoviesTrakt []*TraktWatchedMovie, watchedShowsTrakt []*TraktWatchedShow, toWatchMoviesTrakt []*TraktToWatchMovie) error {

	log.Println("Getting movie details")
	configReq := prepareTmdbReq("/configuration", list.tmdbAuthInfo)
	config := &tmdbConfig{}
	err := doReqAndMarshal(configReq, list.httpClient, config)
	if err != nil {
		return err
	}

	watchedMovieChan := make(chan *TmdbMovie, len(watchedMoviesTrakt))
	watchedShowChan := make(chan *TmdbShow, len(watchedShowsTrakt))
	toWatchMovieChan := make(chan *TmdbMovie, len(toWatchMoviesTrakt))

	numPossibleErrors := len(watchedMoviesTrakt) + len(watchedShowsTrakt) + len(toWatchMoviesTrakt)
	errorChan := make(chan error, numPossibleErrors)

	image_base_url := config.Images.SecureBaseURL + config.Images.PosterSizes[len(config.Images.PosterSizes)-1]
	// TODO move this to a separate function
	_ = image_base_url

	wg := sync.WaitGroup{}

	for _, movie := range watchedMoviesTrakt {
		wg.Add(1)
		go func(movie *TraktWatchedMovie) {
			defer wg.Done()
			list.getMovieData(movie.Movie.Ids.Tmdb, watchedMovieChan, errorChan)
		}(movie)
	}
	for _, show := range watchedShowsTrakt {
		wg.Add(1)
		go func(show *TraktWatchedShow) {
			defer wg.Done()
			list.getShowData(show.Show.Ids.Tmdb, watchedShowChan, errorChan)
		}(show)
	}
	for _, movie := range toWatchMoviesTrakt {
		wg.Add(1)
		go func(movie *TraktToWatchMovie) {
			defer wg.Done()
			list.getMovieData(movie.Movie.Ids.Tmdb, toWatchMovieChan, errorChan)
		}(movie)
	}

	wg.Wait()
	close(errorChan)
	close(watchedMovieChan)
	close(watchedShowChan)
	close(toWatchMovieChan)

	watchedMovies := []*TmdbMovie{}
	for i := 0; i < len(watchedMovieChan); i++ {
		watchedMovies = append(watchedMovies, <-watchedMovieChan)
	}

	tmdbIdToMovie := make(map[int]*TmdbMovie)
	tmdbIdToShow := make(map[int]*TmdbShow)

	for show := range watchedShowChan {
		tmdbIdToShow[show.ID] = show
	}
	for movie := range toWatchMovieChan {
		tmdbIdToMovie[movie.ID] = movie
	}
	for movie := range watchedMovieChan {
		tmdbIdToMovie[movie.ID] = movie
	}

	for _, movie := range watchedMoviesTrakt {
		list.WatchedMovies = append(list.WatchedMovies, &WatchedMovie{
			TmdbMovie:         tmdbIdToMovie[movie.Movie.Ids.Tmdb],
			TraktWatchedMovie: movie,
		})
	}

	for _, movie := range toWatchMoviesTrakt {
		list.ToWatchMovies = append(list.ToWatchMovies, &ToWatchMovie{
			TmdbMovie:         tmdbIdToMovie[movie.Movie.Ids.Tmdb],
			TraktToWatchMovie: movie,
		})
	}

	for _, show := range watchedShowsTrakt {
		list.WatchedShows = append(list.WatchedShows, &WatchedShow{
			TmdbShow:         tmdbIdToShow[show.Show.Ids.Tmdb],
			TraktWatchedShow: show,
		})
	}

	for _, show := range list.WatchedShows {
		if show.TmdbShow == nil {
			fmt.Printf("WARNING: Show %v doesn't have a tmdb entry. TmdbId %v\n", show.TraktWatchedShow.Show.Title, show.TraktWatchedShow.Show.Ids.Tmdb)
			continue
		}
		total := show.TmdbShow.NumberOfEpisodes
		episodesWatched := 0

		for _, watchedShow := range show.TraktWatchedShow.Seasons {
			episodesWatched += len(watchedShow.Episodes)
		}
		show.TotalEpisodes = total
		show.EpisodesWatched = episodesWatched
	}
	errorMessages := []string{}
	for i := 0; i < len(errorChan); i++ {
		err := <-errorChan
		if err != nil {
			errorMessages = append(errorMessages, err.Error())
		}
	}

	if len(errorChan) > 0 {
		return fmt.Errorf("Number of errors: %d, all errors: %s", len(errorChan), strings.Join(errorMessages, ","))
	} else {
		return nil
	}
}
