package traktv

import (
	"bytes"
	"encoding/json"
	"github.com/hashicorp/go-retryablehttp"
	"github.com/skamensky/skam.dev/internal/db"
	"io/ioutil"
	"log"
)

func prepareTmdbReq(url string, authInfo *db.MediaAuth) *retryablehttp.Request {
	req_url := TMDB_BASE_URL + url
	req, err := retryablehttp.NewRequest(
		"GET",
		req_url,
		nil,
	)
	if err != nil {
		panic(err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+authInfo.APISecret)
	return req
}

func doReq(req *retryablehttp.Request, client *retryablehttp.Client) ([]byte, error) {
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}

	defer resp.Body.Close()
	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	return data, nil

}
func doReqAndMarshal[T any](req *retryablehttp.Request, client *retryablehttp.Client, obj *T) error {
	data, err := doReq(req, client)
	if err != nil {
		return err
	}
	err = json.Unmarshal(data, obj)
	if err != nil {
		log.Printf("Failed json data: %v\n", string(data))
		return err
	}
	return nil
}

func prepareTraktReq(method string, url string, jsonBody map[string]string, authInfo *db.MediaAuth) *retryablehttp.Request {
	req_url := TRAKT_BASE_URL + url
	req, err := retryablehttp.NewRequest(
		method,
		req_url,
		nil,
	)
	if err != nil {
		panic(err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("trakt-api-version", "2")
	req.Header.Set("trakt-api-key", authInfo.APIKey)
	if jsonBody != nil {
		jsonBodyMarshalled, err := json.Marshal(jsonBody)
		if err != nil {
			panic(err)
		}
		req.Body = ioutil.NopCloser(bytes.NewBuffer(jsonBodyMarshalled))
	}
	if authInfo.Token != "" {
		req.Header.Set("Authorization", "Bearer "+authInfo.Token)
	}
	return req
}
