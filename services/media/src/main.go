package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type Response struct {
	Service   string    `json:"service"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Status    string    `json:"status"`
}

type HealthResponse struct {
	Status    string    `json:"status"`
	Service   string    `json:"service"`
	Timestamp time.Time `json:"timestamp"`
	Uptime    string    `json:"uptime"`
}

var startTime = time.Now()

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "80"
	}

	serviceName := os.Getenv("SERVICE_NAME")
	if serviceName == "" {
		serviceName = "unknown"
	}

	http.HandleFunc("/", homeHandler(serviceName))
	http.HandleFunc("/health", healthHandler(serviceName))
	http.HandleFunc("/api/status", statusHandler(serviceName))

	log.Printf("🚀 %s service listening on port %s", serviceName, port)
	log.Printf("📊 Health check: http://localhost:%s/health", port)
	
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal("Server failed to start:", err)
	}
}

func homeHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}

		html := fmt.Sprintf(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s Service</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
            min-height: 100vh;
            color: white;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 { margin-bottom: 1rem; }
        .info { margin: 1rem 0; padding: 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 8px; }
        .links a {
            display: inline-block;
            margin: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .links a:hover { background: rgba(255, 255, 255, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 %s Service</h1>
        <div class="info">
            <p><strong>Status:</strong> Running</p>
            <p><strong>Language:</strong> Go</p>
            <p><strong>Timestamp:</strong> %s</p>
        </div>
        <div class="links">
            <a href="/health">Health Check</a>
            <a href="/api/status">API Status</a>
        </div>
    </div>
</body>
</html>`, serviceName, serviceName, time.Now().Format(time.RFC3339))

		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(html))
	}
}

func healthHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uptime := time.Since(startTime)
		
		response := HealthResponse{
			Status:    "healthy",
			Service:   serviceName,
			Timestamp: time.Now(),
			Uptime:    uptime.String(),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}
}

func statusHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := Response{
			Service:   serviceName,
			Message:   fmt.Sprintf("Hello from %s", serviceName),
			Timestamp: time.Now(),
			Status:    "running",
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}
}