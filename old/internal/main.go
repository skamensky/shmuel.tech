package main

import (
	"github.com/skamensky/skam.dev/internal/db"
	"github.com/skamensky/skam.dev/internal/media"
)

func main() {
	err := db.InitializeData()
	if err != nil {
		panic(err)
	}
	err = media.RefreshAllMediaItems()
	if err != nil {
		panic(err)
	}
}
