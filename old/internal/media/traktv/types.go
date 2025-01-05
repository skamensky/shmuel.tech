package traktv

import (
	"fmt"
	"io"
	"strconv"
	"time"
)

// Structs to represent data returned from Trakt.tv/Tmdb APIs
// All types generated using https://mholt.github.io/json-to-go/

type TraktToWatchMovie struct {
	Rank     int         `json:"rank,omitempty"`
	ID       int         `json:"id,omitempty"`
	ListedAt time.Time   `json:"listed_at,omitempty"`
	Notes    interface{} `json:"notes,omitempty"`
	Type     string      `json:"type,omitempty"`
	Movie    TraktEntry  `json:"movie,omitempty"`
}

type TraktIds struct {
	Trakt int    `json:"trakt,omitempty"`
	Slug  string `json:"slug,omitempty"`
	Imdb  string `json:"imdb,omitempty"`
	Tmdb  int    `json:"tmdb,omitempty"`
}
type TraktEntry struct {
	parent *TraktItemList
	Title  string   `json:"title,omitempty"`
	Year   int      `json:"year,omitempty"`
	Ids    TraktIds `json:"ids,omitempty"`
}

type TraktWatchedMovie struct {
	Plays         int        `json:"plays,omitempty"`
	LastWatchedAt time.Time  `json:"last_watched_at,omitempty"`
	LastUpdatedAt time.Time  `json:"last_updated_at,omitempty"`
	Movie         TraktEntry `json:"movie,omitempty"`
}

type TraktWatchedShow struct {
	Plays         int           `json:"plays,omitempty"`
	LastWatchedAt time.Time     `json:"last_watched_at,omitempty"`
	LastUpdatedAt time.Time     `json:"last_updated_at,omitempty"`
	ResetAt       interface{}   `json:"reset_at,omitempty"`
	Show          TraktEntry    `json:"show,omitempty"`
	Seasons       []TraktSeason `json:"seasons,omitempty"`
}

type TraktEpisode struct {
	Number        int       `json:"number,omitempty"`
	Plays         int       `json:"plays,omitempty"`
	LastWatchedAt time.Time `json:"last_watched_at,omitempty"`
}
type TraktSeason struct {
	Number   int            `json:"number,omitempty"`
	Episodes []TraktEpisode `json:"episodes,omitempty"`
}

type TmdbBelongsToCollection struct {
	ID           int    `json:"id,omitempty"`
	Name         string `json:"name,omitempty"`
	PosterPath   string `json:"poster_path,omitempty"`
	BackdropPath string `json:"backdrop_path,omitempty"`
}

type TmdbShow struct {
	BackdropPath   string          `json:"backdrop_path,omitempty"`
	CreatedBy      []TmdbCreatedBy `json:"created_by,omitempty"`
	EpisodeRunTime []int           `json:"episode_run_time,omitempty"`
	FirstAirDate   string          `json:"first_air_date,omitempty"`

	Genres              []TmdbGenre             `json:"genres,omitempty"`
	Homepage            string                  `json:"homepage,omitempty"`
	ID                  int                     `json:"id,omitempty"`
	InProduction        bool                    `json:"in_production,omitempty"`
	Languages           []string                `json:"languages,omitempty"`
	LastAirDate         string                  `json:"last_air_date,omitempty"`
	LastEpisodeToAir    TmdbEpisode             `json:"last_episode_to_air,omitempty"`
	Name                string                  `json:"name,omitempty"`
	NextEpisodeToAir    TmdbEpisode             `json:"next_episode_to_air,omitempty"`
	Networks            []TmdbNetwork           `json:"networks,omitempty"`
	NumberOfEpisodes    int                     `json:"number_of_episodes,omitempty"`
	NumberOfSeasons     int                     `json:"number_of_seasons,omitempty"`
	OriginCountry       []string                `json:"origin_country,omitempty"`
	OriginalLanguage    string                  `json:"original_language,omitempty"`
	OriginalName        string                  `json:"original_name,omitempty"`
	Overview            string                  `json:"overview,omitempty"`
	Popularity          float64                 `json:"popularity,omitempty"`
	PosterPath          string                  `json:"poster_path,omitempty"`
	ProductionCompanies []TmdbProductionCompany `json:"production_companies,omitempty"`
	ProductionCountries []TmdbProductionCountry `json:"production_countries,omitempty"`
	Seasons             []TmdbSeason            `json:"seasons,omitempty"`
	SpokenLanguages     []TmdbSpokenLanguages   `json:"spoken_languages,omitempty"`
	Status              string                  `json:"status,omitempty"`
	Tagline             string                  `json:"tagline,omitempty"`
	Type                string                  `json:"type,omitempty"`
	VoteAverage         float64                 `json:"vote_average,omitempty"`
	VoteCount           int                     `json:"vote_count,omitempty"`
}
type TmdbCreatedBy struct {
	ID          int    `json:"id,omitempty"`
	CreditID    string `json:"credit_id,omitempty"`
	Name        string `json:"name,omitempty"`
	Gender      int    `json:"gender,omitempty"`
	ProfilePath string `json:"profile_path,omitempty"`
}
type TmdbGenre struct {
	ID   int    `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
}
type TmdbEpisode struct {
	AirDate        string `json:"air_date,omitempty"`
	EpisodeNumber  int    `json:"episode_number,omitempty"`
	ID             int    `json:"id,omitempty"`
	Name           string `json:"name,omitempty"`
	Overview       string `json:"overview,omitempty"`
	ProductionCode string `json:"production_code,omitempty"`
	Runtime        int    `json:"runtime,omitempty"`
	SeasonNumber   int    `json:"season_number,omitempty"`
	ShowID         int    `json:"show_id,omitempty"`
	StillPath      string `json:"still_path,omitempty"`
}

type TmdbNetwork struct {
	ID            int    `json:"id,omitempty"`
	Name          string `json:"name,omitempty"`
	LogoPath      string `json:"logo_path,omitempty"`
	OriginCountry string `json:"origin_country,omitempty"`
}
type TmdbProductionCompany struct {
	ID            int    `json:"id,omitempty"`
	LogoPath      string `json:"logo_path,omitempty"`
	Name          string `json:"name,omitempty"`
	OriginCountry string `json:"origin_country,omitempty"`
}
type TmdbProductionCountry struct {
	Iso31661 string `json:"iso_3166_1,omitempty"`
	Name     string `json:"name,omitempty"`
}
type TmdbSeason struct {
	AirDate      string `json:"air_date,omitempty"`
	EpisodeCount int    `json:"episode_count,omitempty"`
	ID           int    `json:"id,omitempty"`
	Name         string `json:"name,omitempty"`
	PosterPath   string `json:"poster_path,omitempty"`
	SeasonNumber int    `json:"season_number,omitempty"`
	Overview     string `json:"overview,omitempty"`
}
type TmdbSpokenLanguages struct {
	EnglishName string `json:"english_name,omitempty"`
	Iso6391     string `json:"iso_639_1,omitempty"`
	Name        string `json:"name,omitempty"`
}

type TmdbMovie struct {
	BackdropPath        string                  `json:"backdrop_path,omitempty"`
	BelongsToCollection TmdbBelongsToCollection `json:"belongs_to_collection,omitempty"`
	Budget              int                     `json:"budget,omitempty"`
	Genres              []TmdbGenre             `json:"genres,omitempty"`
	Homepage            string                  `json:"homepage,omitempty"`
	ID                  int                     `json:"id,omitempty"`
	ImdbID              string                  `json:"imdb_id,omitempty"`
	OriginalLanguage    string                  `json:"original_language,omitempty"`
	OriginalTitle       string                  `json:"original_title,omitempty"`
	Overview            string                  `json:"overview,omitempty"`
	Popularity          float64                 `json:"popularity,omitempty"`
	PosterPath          string                  `json:"poster_path,omitempty"`
	ProductionCompanies []TmdbProductionCompany `json:"production_companies,omitempty"`
	ProductionCountries []TmdbProductionCountry `json:"production_countries,omitempty"`
	ReleaseDate         string                  `json:"release_date,omitempty"`
	Revenue             int                     `json:"revenue,omitempty"`
	Runtime             int                     `json:"runtime,omitempty"`
	SpokenLanguages     []TmdbSpokenLanguages   `json:"spoken_languages,omitempty"`
	Status              string                  `json:"status,omitempty"`
	Tagline             string                  `json:"tagline,omitempty"`
	Title               string                  `json:"title,omitempty"`
	VoteAverage         float64                 `json:"vote_average,omitempty"`
	VoteCount           int                     `json:"vote_count,omitempty"`
}

type tmdbConfig struct {
	Images struct {
		BaseURL       string   `json:"base_url"`
		SecureBaseURL string   `json:"secure_base_url"`
		BackdropSizes []string `json:"backdrop_sizes"`
		LogoSizes     []string `json:"logo_sizes"`
		PosterSizes   []string `json:"poster_sizes"`
		ProfileSizes  []string `json:"profile_sizes"`
		StillSizes    []string `json:"still_sizes"`
	} `json:"images"`
	ChangeKeys []string `json:"change_keys"`
}

type traktDeviceCodeResponse struct {
	DeviceCode      string `json:"device_code"`
	UserCode        string `json:"user_code"`
	VerificationURL string `json:"verification_url"`
	ExpiresIn       int    `json:"expires_in"`
	Interval        int    `json:"interval"`
}

type traktTokenResponse struct {
	AccessToken  string `json:"access_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	RefreshToken string `json:"refresh_token"`
	Scope        string `json:"scope"`
	CreatedAt    int    `json:"created_at"`
}

// structs that we define
type WatchedShow struct {
	*TraktWatchedShow
	*TmdbShow
	TotalEpisodes   int
	EpisodesWatched int
	Progress        float64
}
type WatchedMovie struct {
	*TraktWatchedMovie
	*TmdbMovie
}

type ToWatchMovie struct {
	*TraktToWatchMovie
	*TmdbMovie
}

func (s *TmdbShow) GetPosterKey() string {
	return fmt.Sprintf("media/show_and_movies/posters/shows/%v", s.ID)
}

func (s *TmdbMovie) GetPosterKey() string {
	return fmt.Sprintf("media/show_and_movies/posters/movies/%v", s.ID)
}

func (e *TraktEntry) Id() string {
	return strconv.Itoa(e.Ids.Trakt)

}

func (entry *TraktEntry) Name() string {
	return entry.Title
}

func (entry *TraktEntry) DownloadThumbnail() io.ReadCloser {
	return nil
}

func (ws *WatchedShow) DownloadThumbnail() io.ReadCloser {
	return ws.DownloadThumbnail()
}
func (m *WatchedMovie) DownloadThumbnail() io.ReadCloser {
	return m.DownloadThumbnail()
}
func (tw *ToWatchMovie) DownloadThumbnail() io.ReadCloser {
	return tw.DownloadThumbnail()
}
