package media

import (
	"github.com/skamensky/skam.dev/internal/media/common"
	"github.com/skamensky/skam.dev/internal/media/traktv"
)

func RefreshAllMediaItems() error {
	traktvvList := traktv.TraktItemList{}
	err := common.RefreshLists([]common.MediaItemList{&traktvvList})
	return err
}
