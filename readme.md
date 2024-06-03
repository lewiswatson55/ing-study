

1. set up a venv or conda env or just use base
2. install requirements.txt: `pip install -r requirements.txt`
3. run `python main.py` to start the server
4. open `127.0.0.1:5000/e/0` in your browser for the first row in the database (or change the number to see other rows)\

The csv being used is the stock "example-for-lewis.csv" you sent over, with the added item2-item5 header/columns.
(the other two .csv files have some changes but i ended up just using the one you sent.)

If the .venv folder is in the directory it might not work if youre not on a mac, so you might have to delete it and recreate it with `python3 -m venv .venv` and then activate it with `source .venv/bin/activate` (or `source .venv/Scripts/activate` on windows)
Then install the requirements like 2. above. Side note: github copilot just auto-completed the above sentence for me, which is pretty cool. You probably know this already but better to have too much info than too little.

The HTML template being used by flask is the humevaljinja.html file.
