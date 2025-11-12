# bookish-barnacle

## Usage

1. Install dependencies with your preferred PEP 517 tool. With [uv](https://github.com/astral-sh/uv) you can simply run the command in step 2 and it will resolve the requirements declared in `pyproject.toml`.
2. Run the scraper:

   ```bash
   uv run python main.py
   ```

The script fetches the Overwatch Heroes page, parses the hero navbox with BeautifulSoup, and prints each hero in order along with the role and the absolute link to their wiki page.
