# 🤝 Contributing Guide

Thank you for considering contributing to **Camera Monitor**!

We welcome all contributions – from simple bug reports to major improvements. Here’s how you can help:

---

## 📂 Project Structure

- `run.py` – Entry point for the app
- `camera_config.json` – Your camera setup
- `database.json` – Where events are logged
- `app/` – Core app logic (routes, monitor, utils)
- `static/`, `templates/` – Frontend assets
- `tests/` – Test files using pytest

---

## 🧑‍💻 How to Contribute

1. **Fork** this repo
2. Create a new branch:  
   `git checkout -b feature/your-feature-name`
3. Make your changes and **commit** clearly:  
   `git commit -m "Add feature X"`
4. Push to your branch:  
   `git push origin feature/your-feature-name`
5. Open a **Pull Request**

---

## ✅ Guidelines

- Format code with [Black](https://black.readthedocs.io/)
- Ensure existing tests pass: `pytest`
- Keep pull requests focused and minimal
- Document your changes in the PR description
- Add tests where appropriate

---

## 📦 Install Dev Dependencies

```bash
pip install -r requirements.txt
pip install black pytest
```

---

## 🙋 Need Help?

Open an [issue](https://github.com/cneate93/camera-monitor/issues) or start a discussion. Thanks for contributing!