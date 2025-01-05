package db

import "gorm.io/datatypes"

type MediaAuth struct {
	ServiceName string `gorm:"primaryKey"`
	Token       string
	Username    string
	Password    string
	APIKey      string
	APISecret   string
	ExtraData   datatypes.JSON
}

type MediaItem struct {
	ID          string `gorm:"primaryKey"`
	Name        string
	Thumbnail   []byte
	ServiceName string
	Data        datatypes.JSON
}
