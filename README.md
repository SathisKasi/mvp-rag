# SATHIS RAG

## Run the Document Chat App

1. Install the project dependencies from the project folder:

	```powershell
	uv sync
	```

2. Create a `.env` file in the project folder and add the API keys required by the configured models:

	```text
	GROQ_API_KEY=your-groq-api-key
	GOOGLE_API_KEY=your-google-api-key
	```

	Keep `.env` private; it is excluded from Git.

3. Start the web app:

	```powershell
	uv run uvicorn web_app:app --reload
	```

4. Open [http://127.0.0.1:8000](http://127.0.0.1:8000), upload a PDF, then ask questions about the uploaded documents.

Uploaded PDF chunks are embedded and stored in the local `chroma_db` collection. The chat retrieves relevant chunks and sends them to the configured language model to draft an answer. The uploaded document itself is not kept in the project folder.

Stop the server with `Ctrl+C` in PowerShell.

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
