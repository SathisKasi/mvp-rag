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

4. Create a `.env` file in the project folder and add your provider API keys:

	```text
	GROQ_API_KEY=your-groq-api-key
	GOOGLE_API_KEY=your-google-api-key
	```

	Replace the example values with your own keys. Keep `.env` private; it is excluded from Git.

5. Start the SATHIS RAG web application:

	```powershell
	uv run uvicorn web_app:app --reload --host 127.0.0.1 --port 8000
	```

6. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Choose or drop in a PDF, wait for indexing to finish, then enter a question or choose a suggested question.

PDF text is split into chunks, embedded, and stored in the local `chroma_db` collection. Relevant text is sent to the configured Google embedding and Groq language-model APIs. The uploaded PDF itself is processed from a temporary file and is not saved in the project folder.

The running server also keeps a bounded in-memory semantic cache for one hour. It reuses an answer only when a new question's embedding is at least 0.98 cosine-similar to a cached question. Uploading a PDF clears the cache, and restarting the server starts with an empty cache. The chat API request and response format are unchanged.

7. When finished, return to PowerShell and press `Ctrl+C` to stop the server.

If port 8000 is already in use, start the app with `--port 8001` and open `http://127.0.0.1:8001` instead.

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
