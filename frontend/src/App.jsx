import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "kma_access_token";

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem(TOKEN_KEY)
  );

  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  const [status, setStatus] = useState(
    "Checking backend..."
  );

  const [question, setQuestion] = useState("");
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] =
    useState(true);
  const [deletingDocumentId, setDeletingDocumentId] =
    useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  useEffect(() => {
    checkBackend();
    initializeAuthentication();
  }, []);

  async function checkBackend() {
    try {
      const response = await fetch(
        `${API_BASE}/health`
      );

      if (!response.ok) {
        throw new Error("Backend unavailable");
      }

      const data = await response.json();
      setStatus(data.status);
    } catch (error) {
      console.error(error);
      setStatus("Backend unavailable");
    }
  }

  async function initializeAuthentication() {
    const storedToken =
      localStorage.getItem(TOKEN_KEY);

    if (!storedToken) {
      setAuthLoading(false);
      setDocumentsLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Session expired");
      }

      const user = await response.json();

      setToken(storedToken);
      setCurrentUser(user);

      await loadDocuments(storedToken);
    } catch (error) {
      console.error(error);
      logout();
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogin(event) {
    event.preventDefault();

    if (!username.trim() || !password) {
      setLoginError(
        "Username and password are required."
      );
      return;
    }

    setLoggingIn(true);
    setLoginError("");

    try {
      const formData = new URLSearchParams();

      formData.append(
        "username",
        username.trim()
      );
      formData.append("password", password);

      const response = await fetch(
        `${API_BASE}/auth/token`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Login failed"
        );
      }

      localStorage.setItem(
        TOKEN_KEY,
        data.access_token
      );

      setToken(data.access_token);

      const userResponse = await fetch(
        `${API_BASE}/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${data.access_token}`,
          },
        }
      );

      if (!userResponse.ok) {
        throw new Error(
          "Login succeeded, but user information could not be loaded."
        );
      }

      const user = await userResponse.json();

      setCurrentUser(user);
      setPassword("");
      setLoginError("");

      await loadDocuments(data.access_token);
    } catch (error) {
      console.error(error);

      setLoginError(error.message);
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setCurrentUser(null);
    } finally {
      setLoggingIn(false);
      setAuthLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);

    setToken(null);
    setCurrentUser(null);
    setDocuments([]);
    setResults(null);
    setQuestion("");
    setSearchError("");
    setUploadMessage("");
    setDocumentsLoading(false);
  }

  async function authenticatedFetch(
    url,
    options = {}
  ) {
    const activeToken =
      token ||
      localStorage.getItem(TOKEN_KEY);

    if (!activeToken) {
      throw new Error("Not authenticated");
    }

    const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${activeToken}`,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      logout();
      throw new Error(
        "Your session has expired."
      );
    }

    return response;
  }

  async function loadDocuments(
    activeToken = token
  ) {
    setDocumentsLoading(true);

    try {
      const response = await authenticatedFetch(
        `${API_BASE}/documents`,
        {
          headers: activeToken
            ? {
                Authorization: `Bearer ${activeToken}`,
              }
            : {},
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load documents."
        );
      }

      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error(error);

      if (
        error.message !==
        "Your session has expired."
      ) {
        setDocuments([]);
      }
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await authenticatedFetch(
        `${API_BASE}/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed."
        );
      }

      setUploadMessage(
        `${file.name} uploaded successfully. ${data.chunks_created} chunk(s) created.`
      );

      await loadDocuments();
    } catch (error) {
      console.error(error);

      setUploadMessage(
        `Upload failed: ${error.message}`
      );
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleDelete(
    documentId,
    filename
  ) {
    const confirmed = window.confirm(
      `Delete "${filename}" from the knowledge base?`
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(documentId);
    setUploadMessage("");

    try {
      const response = await authenticatedFetch(
        `${API_BASE}/documents/${documentId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Delete failed."
        );
      }

      setUploadMessage(
        `${filename} was deleted successfully.`
      );

      await loadDocuments();
    } catch (error) {
      console.error(error);

      setUploadMessage(
        `Delete failed: ${error.message}`
      );
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function handleSearch() {
    if (!question.trim() || searching) {
      return;
    }

    setSearching(true);
    setSearchError("");

    try {
      const response = await authenticatedFetch(
        `${API_BASE}/documents/ask?question=${encodeURIComponent(
          question.trim()
        )}`
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.detail ||
            "Search request failed."
        );
      }

      const data = await response.json();

      setResults(data);
    } catch (error) {
      console.error(error);

      if (
        error.message ===
        "Your session has expired."
      ) {
        return;
      }

      setSearchError(error.message);
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  function handleQuestionKeyDown(event) {
    if (
      event.key === "Enter" &&
      event.ctrlKey
    ) {
      event.preventDefault();
      handleSearch();
    }
  }

  if (authLoading) {
    return (
      <div className="login-page">
        <p>Checking authentication...</p>
      </div>
    );
  }

  if (!token || !currentUser) {
    return (
      <div className="login-page">
        <div className="login-card">
          <h1>Knowledge Management</h1>

          <p className="login-description">
            Sign in to access your
            organization's knowledge base.
          </p>

          <form onSubmit={handleLogin}>
            <label className="login-field">
              <span>Username</span>

              <input
                type="text"
                value={username}
                onChange={(event) =>
                  setUsername(
                    event.target.value
                  )
                }
                autoComplete="username"
                autoFocus
              />
            </label>

            <label className="login-field">
              <span>Password</span>

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                autoComplete="current-password"
              />
            </label>

            {loginError && (
              <div
                className="login-error"
                role="alert"
              >
                {loginError}
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loggingIn}
            >
              {loggingIn
                ? "Signing in..."
                : "Sign In"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <h1>Knowledge Management</h1>

          <span className="status">
            <span className="status-dot"></span>
            {status}
          </span>
        </div>

        <div className="header-actions">
          <span className="user-info">
            {currentUser.username} (
            {currentUser.role})
          </span>

          <button
            type="button"
            className="logout-button"
            onClick={logout}
          >
            Logout
          </button>

          <input
            type="file"
            id="document-upload"
            accept=".txt,.pdf"
            style={{ display: "none" }}
            onChange={handleUpload}
            disabled={uploading}
          />

          <label
            htmlFor="document-upload"
            className={`upload-button ${
              uploading ? "disabled" : ""
            }`}
          >
            {uploading
              ? "Uploading..."
              : "Upload Document"}
          </label>
        </div>

        {uploadMessage && (
          <div
            className="upload-message"
            role="status"
          >
            {uploadMessage}
          </div>
        )}
      </header>

      <main className="main">
        <section className="welcome">
          <h2>Ask your knowledge base</h2>

          <p>
            Search your organization's
            documents and get answers grounded
            in your stored knowledge.
          </p>
        </section>

        <section className="search-card">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              handleSearch();
            }}
          >
            <label
              htmlFor="question"
              className="question-label"
            >
              Ask a question
            </label>

            <textarea
              id="question"
              name="question"
              placeholder="Ask a question about your organization's knowledge..."
              rows="4"
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              onKeyDown={
                handleQuestionKeyDown
              }
              aria-describedby="question-help"
            />

            <div className="search-footer">
              <span id="question-help">
                Press Ctrl+Enter to submit.
              </span>

              <button
                type="submit"
                className="ask-button"
                disabled={
                  searching ||
                  !question.trim()
                }
              >
                {searching
                  ? "Searching..."
                  : "Ask"}
              </button>
            </div>
          </form>
        </section>

        <section className="results">
          <h3>Answer</h3>

          {searching ? (
            <div className="searching-answer">
              <p>
                Searching the knowledge base...
              </p>
            </div>
          ) : searchError ? (
            <div
              className="answer-error"
              role="alert"
            >
              {searchError}
            </div>
          ) : results === null ? (
            <div className="empty-answer">
              <p>
                Your answer will appear here.
              </p>

              <span>
                Supporting documents will be
                displayed below the answer.
              </span>
            </div>
          ) : (
            <div className="search-results">
              <ReactMarkdown>
                {results.answer}
              </ReactMarkdown>

              {results.sources.length > 0 && (
                <>
                  <h4 className="sources-heading">
                    Sources
                  </h4>

                  {results.sources.map(
                    (source, index) => (
                      <div
                        className="result-item"
                        key={`${source.document_id}-${index}`}
                      >
                        <strong>
                          {source.document}
                        </strong>

                        <p>
                          {source.content}
                        </p>
                      </div>
                    )
                  )}
                </>
              )}
            </div>
          )}
        </section>

        <section className="documents">
          <div className="documents-header">
            <div>
              <h3>Documents</h3>

              <span>
                {documents.length} document
                {documents.length === 1
                  ? ""
                  : "s"} in the knowledge base
              </span>
            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={() =>
                loadDocuments()
              }
              disabled={documentsLoading}
            >
              {documentsLoading
                ? "Loading..."
                : "Refresh"}
            </button>
          </div>

          {documentsLoading ? (
            <div className="documents-empty">
              Loading documents...
            </div>
          ) : documents.length === 0 ? (
            <div className="documents-empty">
              No documents have been uploaded yet.
            </div>
          ) : (
            <div className="document-list">
              {documents.map((document) => (
                <div
                  className="document-item"
                  key={document.id}
                >
                  <div className="document-icon">
                    {document.filename
                      .toLowerCase()
                      .endsWith(".pdf")
                      ? "PDF"
                      : "TXT"}
                  </div>

                  <div className="document-info">
                    <strong>
                      {document.filename}
                    </strong>

                    <span>
                      Document ID:{" "}
                      {document.id}
                    </span>
                  </div>

                  <button
                    type="button"
                    className="delete-button"
                    onClick={() =>
                      handleDelete(
                        document.id,
                        document.filename
                      )
                    }
                    disabled={
                      deletingDocumentId ===
                      document.id
                    }
                  >
                    {deletingDocumentId ===
                    document.id
                      ? "Deleting..."
                      : "Delete"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
