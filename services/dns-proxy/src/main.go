package main

import (
	"crypto/subtle"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

type DNSProxyRequest struct {
	APIUser   string            `json:"api_user"`
	APIKey    string            `json:"api_key"`
	ClientIP  string            `json:"client_ip"`
	Command   string            `json:"command"`
	Data      map[string]string `json:"data"`
	ProxyAuth string            `json:"proxy_auth"`
	Sandbox   bool              `json:"sandbox"`
}

type DNSProxyResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

type NamecheapBaseResponse struct {
	XMLName xml.Name `xml:"ApiResponse"`
	Status  string   `xml:"Status,attr"`
	Errors  []struct {
		Number string `xml:"Number,attr"`
		Text   string `xml:",chardata"`
	} `xml:"Errors>Error"`
}

type NamecheapGetHostsResponse struct {
	NamecheapBaseResponse
	CommandResponse struct {
		Type    string `xml:"Type,attr"`
		GetHostsResult struct {
			Domain        string `xml:"Domain,attr"`
			EmailType     string `xml:"EmailType,attr"`
			IsUsingOurDNS string `xml:"IsUsingOurDNS,attr"`
			Hosts         []Host `xml:"host"`
		} `xml:"DomainDNSGetHostsResult"`
	} `xml:"CommandResponse"`
}

type NamecheapSetHostsResponse struct {
	NamecheapBaseResponse
	CommandResponse struct {
		Type    string `xml:"Type,attr"`
		SetHostsResult struct {
			IsSuccess string `xml:"IsSuccess,attr"`
		} `xml:"DomainDNSSetHostsResult"`
	} `xml:"CommandResponse"`
}

type Host struct {
	HostId     string `xml:"HostId,attr"`
	Name       string `xml:"Name,attr"`
	Type       string `xml:"Type,attr"`
	Address    string `xml:"Address,attr"`
	MXPref     string `xml:"MXPref,attr"`
	TTL        string `xml:"TTL,attr"`
	IsActive   string `xml:"IsActive,attr"`
	IsDDNSEnabled string `xml:"IsDDNSEnabled,attr"`
}

type HealthResponse struct {
	Status    string    `json:"status"`
	Service   string    `json:"service"`
	Timestamp time.Time `json:"timestamp"`
	Uptime    string    `json:"uptime"`
	SupportedEnvironments []string `json:"supported_environments"`
}

// ResponseWriter wrapper to capture status code and response size
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	size       int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	size, err := rw.ResponseWriter.Write(b)
	rw.size += size
	return size, err
}

// Logging middleware for comprehensive access logging
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Wrap the ResponseWriter
		wrapped := &responseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK, // Default status code
		}
		
		// Get request body size
		requestSize := int64(0)
		if r.ContentLength > 0 {
			requestSize = r.ContentLength
		}
		
		// Process the request
		next.ServeHTTP(wrapped, r)
		
		// Calculate duration
		duration := time.Since(start)
		
		// Log the request with structured logging
		slog.Info("HTTP Request",
			slog.String("method", r.Method),
			slog.String("path", r.URL.Path),
			slog.String("query", r.URL.RawQuery),
			slog.String("remote_addr", r.RemoteAddr),
			slog.String("user_agent", r.UserAgent()),
			slog.String("referer", r.Referer()),
			slog.String("host", r.Host),
			slog.String("proto", r.Proto),
			slog.Int64("request_size", requestSize),
			slog.Int("response_size", wrapped.size),
			slog.Int("status_code", wrapped.statusCode),
			slog.Duration("duration", duration),
			slog.String("duration_ms", fmt.Sprintf("%.2f", duration.Seconds()*1000)),
		)
	})
}

var startTime = time.Now()

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "80"
	}

	serviceName := os.Getenv("SERVICE_NAME")
	if serviceName == "" {
		serviceName = "dns-proxy"
	}

	// Check if PROXY_AUTH_TOKEN is set
	proxyAuthToken := os.Getenv("PROXY_AUTH_TOKEN")
	if proxyAuthToken == "" {
		log.Fatal("PROXY_AUTH_TOKEN environment variable is required")
	}

	// Configure structured logging
	logLevel := slog.LevelInfo
	if os.Getenv("LOG_LEVEL") == "debug" {
		logLevel = slog.LevelDebug
	}

	// Set up JSON logging for production or text for development
	var handler slog.Handler
	if os.Getenv("LOG_FORMAT") == "json" {
		handler = slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
			Level: logLevel,
		})
	} else {
		handler = slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
			Level: logLevel,
		})
	}

	logger := slog.New(handler)
	slog.SetDefault(logger)

	// Log startup information
	slog.Info("DNS Proxy Service Starting",
		slog.String("service", serviceName),
		slog.String("port", port),
		slog.String("log_level", logLevel.String()),
	)

	// Set up HTTP routes with logging middleware
	mux := http.NewServeMux()
	mux.HandleFunc("/", homeHandler(serviceName))
	mux.HandleFunc("/health", healthHandler(serviceName))
	mux.HandleFunc("/api/dns", dnsProxyHandler(proxyAuthToken))

	// Wrap the mux with logging middleware
	httpHandler := loggingMiddleware(mux)

	slog.Info("Service Configuration",
		slog.String("endpoints", "/health, /api/dns"),
		slog.String("api_environments", "production & sandbox"),
		slog.String("health_check_url", fmt.Sprintf("http://localhost:%s/health", port)),
		slog.String("dns_proxy_url", fmt.Sprintf("http://localhost:%s/api/dns", port)),
	)

	slog.Info("Server starting", slog.String("address", ":"+port))

	if err := http.ListenAndServe(":"+port, httpHandler); err != nil {
		slog.Error("Server failed to start", slog.String("error", err.Error()))
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
    <title>DNS Proxy Service</title>
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
        .environment { background: rgba(33, 150, 243, 0.2); border: 1px solid rgba(33, 150, 243, 0.5); font-weight: bold; }
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
        .warning { background: rgba(255, 193, 7, 0.2); border: 1px solid rgba(255, 193, 7, 0.5); }
        .feature { background: rgba(76, 175, 80, 0.2); border: 1px solid rgba(76, 175, 80, 0.5); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 DNS Proxy Service</h1>
        <div class="info environment">
            <p>🔄 Multi-Environment Support</p>
            <p>Per-request Production & Sandbox routing</p>
        </div>
        <div class="info">
            <p><strong>Status:</strong> Running</p>
            <p><strong>Purpose:</strong> Namecheap API Proxy</p>
            <p><strong>Language:</strong> Go</p>
            <p><strong>Configuration:</strong> Per-request environment selection</p>
            <p><strong>Timestamp:</strong> %s</p>
        </div>
        <div class="info feature">
            <p><strong>✨ Flexible Configuration:</strong></p>
            <p>Each request can specify production or sandbox mode</p>
            <p>Single proxy handles both environments</p>
        </div>
        <div class="info warning">
            <p><strong>⚠️ Security Notice:</strong></p>
            <p>This service requires proper authentication.</p>
            <p>Unauthorized access attempts are logged and blocked.</p>
        </div>
        <div class="links">
            <a href="/health">Health Check</a>
        </div>
    </div>
</body>
</html>`, time.Now().Format(time.RFC3339))

		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(html))
	}
}

func healthHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uptime := time.Since(startTime)

		response := HealthResponse{
			Status:                "healthy",
			Service:               serviceName,
			Timestamp:             time.Now(),
			Uptime:                uptime.String(),
			SupportedEnvironments: []string{"production", "sandbox"},
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}
}

func dnsProxyHandler(proxyAuthToken string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Only accept POST requests
		if r.Method != http.MethodPost {
			slog.Warn("Invalid HTTP method attempted",
				slog.String("method", r.Method),
				slog.String("remote_addr", r.RemoteAddr),
				slog.String("user_agent", r.UserAgent()),
			)
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		// Parse JSON request
		var req DNSProxyRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			slog.Warn("Invalid JSON payload received",
				slog.String("error", err.Error()),
				slog.String("remote_addr", r.RemoteAddr),
				slog.String("user_agent", r.UserAgent()),
			)
			respondWithError(w, "Invalid JSON payload", http.StatusBadRequest)
			return
		}

		// Validate proxy authentication - constant time comparison for security
		if subtle.ConstantTimeCompare([]byte(req.ProxyAuth), []byte(proxyAuthToken)) != 1 {
			slog.Warn("Authentication failed - unauthorized access attempt",
				slog.String("remote_addr", r.RemoteAddr),
				slog.String("user_agent", r.UserAgent()),
				slog.String("api_user", req.APIUser),
				slog.Bool("sandbox", req.Sandbox),
				slog.String("provided_token_length", fmt.Sprintf("%d", len(req.ProxyAuth))),
				slog.String("expected_token_length", fmt.Sprintf("%d", len(proxyAuthToken))),
			)
			respondWithError(w, "Authentication failed", http.StatusUnauthorized)
			return
		}

		// Determine API endpoint based on request
		apiEndpoint := "https://api.namecheap.com/xml.response"
		environment := "production"
		if req.Sandbox {
			apiEndpoint = "https://api.sandbox.namecheap.com/xml.response"
			environment = "sandbox"
		}

		// Log successful authentication and request details
		slog.Info("DNS proxy request authenticated",
			slog.String("command", req.Command),
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
			slog.String("environment", environment),
			slog.String("remote_addr", r.RemoteAddr),
			slog.String("auth_token_length", fmt.Sprintf("%d", len(req.ProxyAuth))),
		)

		// Handle the DNS command
		switch req.Command {
		case "namecheap.domains.dns.getHosts":
			handleGetHosts(w, req, apiEndpoint)
		case "namecheap.domains.dns.setHosts":
			handleSetHosts(w, req, apiEndpoint)
		default:
			slog.Warn("Unsupported command requested",
				slog.String("command", req.Command),
				slog.String("api_user", req.APIUser),
				slog.String("remote_addr", r.RemoteAddr),
			)
			respondWithError(w, "Unsupported command", http.StatusBadRequest)
		}
	}
}

func handleGetHosts(w http.ResponseWriter, req DNSProxyRequest, apiEndpoint string) {
	start := time.Now()
	
	// Validate required parameters
	domain := req.Data["domain"]
	if domain == "" {
		slog.Warn("getHosts request missing domain parameter",
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
		)
		respondWithError(w, "domain parameter is required", http.StatusBadRequest)
		return
	}

	// Split domain
	parts := strings.Split(domain, ".")
	if len(parts) < 2 {
		slog.Warn("getHosts request with invalid domain format",
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
		)
		respondWithError(w, "Invalid domain format", http.StatusBadRequest)
		return
	}

	slog.Info("Processing getHosts request",
		slog.String("domain", domain),
		slog.String("sld", parts[0]),
		slog.String("tld", parts[1]),
		slog.String("api_user", req.APIUser),
		slog.String("client_ip", req.ClientIP),
	)

	// Prepare Namecheap API request
	params := url.Values{}
	params.Set("ApiUser", req.APIUser)
	params.Set("ApiKey", req.APIKey)
	params.Set("UserName", req.APIUser)
	params.Set("Command", "namecheap.domains.dns.getHosts")
	params.Set("ClientIp", req.ClientIP)
	params.Set("SLD", parts[0])
	params.Set("TLD", parts[1])

	// Make API call
	resp, err := http.Get(apiEndpoint + "?" + params.Encode())
	if err != nil {
		slog.Error("Namecheap API request failed",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("endpoint", apiEndpoint),
		)
		respondWithError(w, fmt.Sprintf("API request failed: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		slog.Error("Failed to read API response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
		)
		respondWithError(w, fmt.Sprintf("Failed to read response: %v", err), http.StatusInternalServerError)
		return
	}

	// Log the raw XML response for debugging
	slog.Debug("Received XML response from Namecheap",
		slog.String("domain", domain),
		slog.String("api_user", req.APIUser),
		slog.String("xml_response", string(body)),
	)

	// First, check for errors in the response
	var baseResp NamecheapBaseResponse
	if err := xml.Unmarshal(body, &baseResp); err != nil {
		slog.Error("Failed to parse XML response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("raw_xml", string(body)),
		)
		respondWithError(w, fmt.Sprintf("Failed to parse XML: %v", err), http.StatusInternalServerError)
		return
	}

	// Check for API errors
	if len(baseResp.Errors) > 0 {
		errorMsg := baseResp.Errors[0].Text
		slog.Warn("Namecheap API returned error",
			slog.String("error", errorMsg),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
		)
		respondWithError(w, fmt.Sprintf("Namecheap API error: %s", errorMsg), http.StatusBadRequest)
		return
	}

	// Parse the full response for successful requests
	var namecheapResp NamecheapGetHostsResponse
	if err := xml.Unmarshal(body, &namecheapResp); err != nil {
		slog.Error("Failed to parse full XML response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("raw_xml", string(body)),
		)
		respondWithError(w, fmt.Sprintf("Failed to parse XML: %v", err), http.StatusInternalServerError)
		return
	}

	// Convert hosts to JSON-friendly format
	hosts := make([]map[string]string, len(namecheapResp.CommandResponse.GetHostsResult.Hosts))
	for i, host := range namecheapResp.CommandResponse.GetHostsResult.Hosts {
		hosts[i] = map[string]string{
			"Name":    host.Name,
			"Type":    host.Type,
			"Address": host.Address,
			"TTL":     host.TTL,
			"MXPref":  host.MXPref,
		}
	}

	duration := time.Since(start)
	slog.Info("getHosts request completed successfully",
		slog.String("domain", domain),
		slog.String("api_user", req.APIUser),
		slog.Int("host_count", len(hosts)),
		slog.Duration("duration", duration),
	)

	respondWithSuccess(w, hosts)
}

func handleSetHosts(w http.ResponseWriter, req DNSProxyRequest, apiEndpoint string) {
	start := time.Now()
	
	// Validate required parameters
	domain := req.Data["domain"]
	if domain == "" {
		slog.Warn("setHosts request missing domain parameter",
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
		)
		respondWithError(w, "domain parameter is required", http.StatusBadRequest)
		return
	}

	// Split domain
	parts := strings.Split(domain, ".")
	if len(parts) < 2 {
		slog.Warn("setHosts request with invalid domain format",
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
		)
		respondWithError(w, "Invalid domain format", http.StatusBadRequest)
		return
	}

	// Prepare Namecheap API request
	params := url.Values{}
	params.Set("ApiUser", req.APIUser)
	params.Set("ApiKey", req.APIKey)
	params.Set("UserName", req.APIUser)
	params.Set("Command", "namecheap.domains.dns.setHosts")
	params.Set("ClientIp", req.ClientIP)
	params.Set("SLD", parts[0])
	params.Set("TLD", parts[1])

	// Add host records
	recordCount := 0
	for key, value := range req.Data {
		if strings.HasPrefix(key, "HostName") {
			recordCount++
			index := strings.TrimPrefix(key, "HostName")
			params.Set(key, value)
			params.Set("RecordType"+index, req.Data["RecordType"+index])
			params.Set("Address"+index, req.Data["Address"+index])
			params.Set("TTL"+index, req.Data["TTL"+index])
			if req.Data["MXPref"+index] != "" {
				params.Set("MXPref"+index, req.Data["MXPref"+index])
			}
		}
	}

	if recordCount == 0 {
		slog.Warn("setHosts request with no host records",
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("client_ip", req.ClientIP),
		)
		respondWithError(w, "No host records provided", http.StatusBadRequest)
		return
	}

	slog.Info("Processing setHosts request",
		slog.String("domain", domain),
		slog.String("sld", parts[0]),
		slog.String("tld", parts[1]),
		slog.String("api_user", req.APIUser),
		slog.String("client_ip", req.ClientIP),
		slog.Int("record_count", recordCount),
	)

	// Log the parameters we're sending to Namecheap
	slog.Debug("Sending parameters to Namecheap",
		slog.String("domain", domain),
		slog.String("api_user", req.APIUser),
		slog.String("params", params.Encode()),
	)

	// Make API call with form data (POST)
	resp, err := http.PostForm(apiEndpoint, params)
	if err != nil {
		slog.Error("Namecheap API request failed",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("endpoint", apiEndpoint),
		)
		respondWithError(w, fmt.Sprintf("API request failed: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		slog.Error("Failed to read API response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
		)
		respondWithError(w, fmt.Sprintf("Failed to read response: %v", err), http.StatusInternalServerError)
		return
	}

	// Log the raw XML response for debugging
	slog.Debug("Received XML response from Namecheap",
		slog.String("domain", domain),
		slog.String("api_user", req.APIUser),
		slog.String("xml_response", string(body)),
	)

	// First, check for errors in the response
	var baseResp NamecheapBaseResponse
	if err := xml.Unmarshal(body, &baseResp); err != nil {
		slog.Error("Failed to parse XML response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("raw_xml", string(body)),
		)
		respondWithError(w, fmt.Sprintf("Failed to parse XML: %v", err), http.StatusInternalServerError)
		return
	}

	// Check for API errors
	if len(baseResp.Errors) > 0 {
		errorMsg := baseResp.Errors[0].Text
		slog.Warn("Namecheap API returned error",
			slog.String("error", errorMsg),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
		)
		respondWithError(w, fmt.Sprintf("Namecheap API error: %s", errorMsg), http.StatusBadRequest)
		return
	}

	// Parse the full response for successful requests
	var namecheapResp NamecheapSetHostsResponse
	if err := xml.Unmarshal(body, &namecheapResp); err != nil {
		slog.Error("Failed to parse full XML response",
			slog.String("error", err.Error()),
			slog.String("domain", domain),
			slog.String("api_user", req.APIUser),
			slog.String("raw_xml", string(body)),
		)
		respondWithError(w, fmt.Sprintf("Failed to parse XML: %v", err), http.StatusInternalServerError)
		return
	}

	// Check if operation was successful
	success := namecheapResp.CommandResponse.SetHostsResult.IsSuccess == "true"
	
	duration := time.Since(start)
	slog.Info("setHosts request completed",
		slog.String("domain", domain),
		slog.String("api_user", req.APIUser),
		slog.Int("record_count", recordCount),
		slog.Bool("success", success),
		slog.Duration("duration", duration),
	)

	respondWithSuccess(w, map[string]interface{}{
		"success": success,
		"recordsUpdated": recordCount,
	})
}

func respondWithError(w http.ResponseWriter, message string, statusCode int) {
	response := DNSProxyResponse{
		Success: false,
		Error:   message,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(response)
}

func respondWithSuccess(w http.ResponseWriter, data interface{}) {
	response := DNSProxyResponse{
		Success: true,
		Data:    data,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}