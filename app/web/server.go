package main

import (
	"embed"
	"io/fs"
	"log"
	"net/http"
	"os"
)

//go:embed dist
var dist embed.FS

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	distFS, err := fs.Sub(dist, "dist")
	if err != nil {
		log.Fatal(err)
	}

	http.Handle("/", spaHandler(http.FileServer(http.FS(distFS))))

	log.Printf("Server listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func spaHandler(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if _, err := dist.Open("dist" + r.URL.Path); err != nil {
			r.URL.Path = "/"
		}
		h.ServeHTTP(w, r)
	})
}
