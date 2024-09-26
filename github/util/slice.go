package util

func FilterNil[T any](slice []*T) []*T {
	filtered := make([]*T, 0)
	for _, item := range slice {
		if item != nil {
			filtered = append(filtered, item)
		}
	}
	return filtered
}
