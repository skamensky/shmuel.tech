package common

import (
	"github.com/skamensky/skam.dev/internal/db"
	"gorm.io/gorm"
	"io"
)

type MediaItemList interface {
	PersistToDB() error
	RetrieveItemsFromDB() ([]MediaItem, error)
	RetrieveItemsFromTracker() ([]MediaItem, error)
	RetrievePrivateIdsFromDB() []string
	Init(*gorm.DB) error
}
type MediaItem interface {
	Id() string
	Name() string
	DownloadThumbnail() io.ReadCloser
}

func RefreshLists(lists []MediaItemList) error {
	DB, err := db.NewDB()
	if err != nil {
		return err
	}
	for _, list := range lists {
		err := list.Init(DB)
		if err != nil {
			return err
		}
		items, err := list.RetrieveItemsFromTracker()
		// TODO, get all thumbnails for items
		_ = items
		if err != nil {
			return err
		}
		err = list.PersistToDB()
		if err != nil {
			return err
		}
	}
	return nil
}
