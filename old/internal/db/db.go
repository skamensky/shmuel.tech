package db

import (
	"fmt"
	"github.com/pkg/errors"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"log"
	"os"
	"strings"
)

func NewDB() (*gorm.DB, error) {
	// todo remove
	os.Setenv("POSTGRES_HOST", "127.0.0.1")
	postgresUser := os.Getenv("POSTGRES_USER")
	postgresPass := os.Getenv("POSTGRES_PASSWORD")
	postgresHost := os.Getenv("POSTGRES_HOST")
	postgresDB := os.Getenv("POSTGRES_DB")
	postgresPort := os.Getenv("POSTGRES_PORT")

	postgresConfig := map[string]string{
		"POSTGRES_USER":     "",
		"POSTGRES_PASSWORD": "",
		"POSTGRES_HOST":     "",
		"POSTGRES_DB":       "",
		"POSTGRES_PORT":     "",
	}

	missing := []string{}
	for k, _ := range postgresConfig {
		postgresConfig[k] = os.Getenv(k)
		if postgresConfig[k] == "" {
			missing = append(missing, k)
		}
	}

	if len(missing) > 0 {
		return nil, fmt.Errorf("Missing postgres env vars: %s", strings.Join(missing, ", "))
	}

	dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s ", postgresHost, postgresUser, postgresPass, postgresDB, postgresPort)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, errors.Wrap(err, "failed to open db")
	} else {
		return db, nil
	}
}

func InitializeData() error {
	db, err := NewDB()
	if err != nil {
		return err
	}
	err = db.AutoMigrate(&MediaAuth{})
	if err != nil {
		return errors.Wrap(err, "failed to migrate media auth")
	}
	err = db.AutoMigrate(&MediaItem{})
	if err != nil {
		return errors.Wrap(err, "failed to migrate media item")
	}
	traktAPIKey := os.Getenv("TRAKT_API_KEY")
	traktSecret := os.Getenv("TRAKT_SECRET")
	traktEmail := os.Getenv("TRAKT_EMAIL")
	traktPassword := os.Getenv("TRAKT_PASSWORD")
	tmdbSecret := os.Getenv("TMDB_SECRET")

	traktAuth := MediaAuth{
		APIKey:      traktAPIKey,
		APISecret:   traktSecret,
		Username:    traktEmail,
		Password:    traktPassword,
		ServiceName: "trakt",
	}
	tmdbAuth := MediaAuth{
		APISecret:   tmdbSecret,
		ServiceName: "tmdb",
	}

	// servicename to auth map
	localAuthMap := map[string]MediaAuth{
		"trakt": traktAuth,
		"tmdb":  tmdbAuth,
	}
	dbAuths := []MediaAuth{}
	res := db.Find(&dbAuths)
	if res.Error != nil {
		return errors.Wrap(res.Error, "failed to find auths")
	}

	dbAuthMap := map[string]MediaAuth{}
	for _, auth := range dbAuths {
		dbAuthMap[auth.ServiceName] = auth
	}

	for serviceName, auth := range localAuthMap {
		if _, ok := dbAuthMap[serviceName]; !ok {
			log.Printf("Auth for service %s is missing in DB. Creating it.", serviceName)
			res := db.Create(&auth)
			if res.Error != nil {
				return errors.Wrap(res.Error, "failed to create auth")
			}
		}
	}

	return nil
}
