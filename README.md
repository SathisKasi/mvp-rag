# SATHIS RAG

## Run the Application

The following steps use Windows PowerShell. You need Python 3.10 or newer and `uv`.

1. Open PowerShell in the project folder:

	```powershell
	cd "D:\Sathis\Example\Python\mvp-rag"
	```

2. Check that `uv` is available. If it is not installed, install it with Python's package installer:

	```powershell
	uv --version
	python -m pip install uv
	```

3. Install or synchronize the project dependencies. Run this again whenever dependencies change:

	```powershell
	uv sync
	```

4. In pgAdmin 4, verify the server connection uses host `localhost` and port `5433`. Under that server's `Databases` node, confirm a database named exactly `mvp-rag` exists. If it is missing, right-click `Databases`, choose **Create > Database**, enter `mvp-rag` as the name, and save. Then connect to that database, open its Query Tool, and enable pgvector:

	```text
	CREATE EXTENSION IF NOT EXISTS vector;
	```

	The application connects to PostgreSQL directly; pgAdmin is used to manage and inspect the database. If PostgreSQL reports that the `vector` extension is unavailable, install pgvector for your PostgreSQL server before continuing.

5. Copy the environment template and edit `.env` locally:

	```powershell
	Copy-Item .env.example .env
	notepad .env
	```

	Enter your Groq and Google API keys and your PostgreSQL password in `.env`. The connection defaults are `localhost:5433`, database `mvp-rag`, and user `postgres`. Keep `.env` private; it is excluded from Git. Do not put credentials in source code or commit them.

6. If you have existing records in the project's `chroma_db` folder that you want to keep, install the optional migration dependency and import the stored text, embeddings, and metadata:

	```powershell
	uv sync --group migration
	uv run python migrate_chroma.py
	```

	This step is optional for a fresh setup. The migration script can be run again safely; already migrated records are skipped.

7. Start the SATHIS RAG web application:

	```powershell
	uv run uvicorn web_app:app --reload --host 127.0.0.1 --port 8000
	```

8. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Choose or drop in one or more PDFs, wait for indexing to finish, then enter a question or choose a suggested question. Previously added documents load from PostgreSQL when the page opens; use the delete button beside a document to remove that file and its indexed vectors.

You can also index PDFs from PowerShell through the same deduplicating upload path:

```powershell
uv run python ingestion.py "D:\Documents\first.pdf" "D:\Documents\second.pdf"
```

PDF text is split into chunks, embedded, and stored in the PostgreSQL `MVP_RAG` pgvector collection. File names, content hashes, and page/chunk counts are tracked in the `rag_documents` table in the same `mvp-rag` database. Relevant text is sent to the configured Google embedding and Groq language-model APIs. The uploaded PDF itself is processed from a temporary file and is not saved in the project folder.

Uploading a PDF with identical file contents again skips chunks already stored in PostgreSQL. If an earlier upload inserted only some chunks, re-uploading adds only the missing chunks. Deleting a listed document removes its vector IDs and registry entry.

The running server also keeps a bounded in-memory semantic cache for one hour. It reuses an answer only when a new question's embedding is at least 0.98 cosine-similar to a cached question. Uploading a PDF clears the cache, and restarting the server starts with an empty cache. The chat API request and response format are unchanged.

Uploads are limited to 25 MB and must have a PDF filename and PDF file signature. Empty or unreadable PDFs and blank or overlong questions are rejected with a clear error. Document excerpts are treated as untrusted input by the assistant, and cache errors fall back to the normal retrieval and answer path.

7. When finished, return to PowerShell and press `Ctrl+C` to stop the server.

If port 8000 is already in use, start the app with `--port 8001` and open `http://127.0.0.1:8001` instead.

If startup reports `database "mvp-rag" does not exist`, the server at the configured host and port does not contain that exact database. Check the server's port in pgAdmin and verify the database name. If the database was created on another port, set `POSTGRES_PORT` in `.env` to that port; otherwise create `mvp-rag` under the server listening on `localhost:5433`.

## Push This Project to GitHub

These steps use PowerShell on Windows. Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` with your GitHub username and repository name.

## First Push

1. Install Git if it is not already installed, then verify it in PowerShell:

	```powershell
	git --version
	```

2. Set the name and email Git should use for your commits. Use the email associated with your GitHub account if you want the commits linked to it:

	```powershell
	git config --global user.name "Your Name"
	git config --global user.email "you@example.com"
	```

3. On GitHub, create a new, empty repository. Do not initialize it with a README, license, or `.gitignore`; this project already has its own files.

4. Open PowerShell in the project folder:

	```powershell
	cd "D:\Sathis\Example\Python\mvp-rag"
	```

5. Initialize Git and check which files will be included. The `.env` file and generated `chroma_db` directory are ignored and should stay local:

	```powershell
	git init
	git branch -M main
	git status
	```

	If `git status` shows API keys, `.env` contents, or other secrets, do not stage or push them. Keep credentials in `.env`, never in committed source files.

6. Stage and commit the project files:

	```powershell
	git add .
	git status
	git commit -m "Initial project upload"
	```

	Review `git status` before committing to make sure only intended files are staged.

7. Connect the local project to your GitHub repository and push the `main` branch:

	```powershell
	git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
	git push -u origin main
	```

	If GitHub asks you to authenticate, complete the browser sign-in or use the credential manager prompt. Do not put a password or access token directly into the remote URL or source files.

8. Refresh the GitHub repository page to see the pushed files.

## Push Later Changes

After editing the project, run these commands from the project folder:

```powershell
git status
git add .
git status
git commit -m "Describe the change"
git push
```

Check the staged changes shown by `git status` before committing. If there is nothing new to commit, Git will say so; there is nothing to push until you create a commit.

## Common Issues

- **`remote origin already exists`:** Check the configured URL with `git remote -v`. To change it, run `git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git`.
- **Authentication failed:** Sign in through Git Credential Manager or the browser prompt. GitHub account passwords are not accepted for HTTPS Git operations.
- **Push rejected because the GitHub repository already has commits:** The simplest route for a new project is to create an empty GitHub repository and retry. If you need to keep its existing files, pull and resolve the histories before pushing.
- **A secret was committed:** Removing it in a later commit does not make it safe; revoke or rotate the exposed key immediately.
