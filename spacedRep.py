from typer import Typer,Argument,Option
import sqlite3
import os.path as os_path
import json
from typing_extensions import Annotated
from datetime import date, timedelta
from rich.table import Table
from rich.console import Console


app = Typer(no_args_is_help=True)

# Global variables
PATH_TO_DB = './spacedRepetition.sqlite3'



@app.command()
def revisable():
    with open("settings.json", "r") as read_file:
        settings = json.load(read_file)
    today = date.today()
    conn = sqlite3.connect(PATH_TO_DB)
    cursor = conn.cursor()
    sql_query_text = 'SELECT rowid,* FROM subject_tracking WHERE '
    revision_column_name = settings['revision_column_name']
    for item in range(len(revision_column_name)):
        sql_query_text = sql_query_text + f'"{revision_column_name[item]}" = "{today}"'
        if item != len(settings['revision_column_name']) - 1:
            sql_query_text = sql_query_text + ' OR'
    result = cursor.execute(sql_query_text)
    table_headers = ['ID','Subject','Topics','Starting Date']
    for elem in range(settings["number_of_repetition"]):
        table_headers.append(f'Revision{elem + 1}')
    table = Table(*table_headers)
    for item in result:
        row_elements = []
        for elem in item:
            row_elements.append(str(elem))
        table.add_row(*row_elements)
        
    console = Console()
    console.print(table)
    conn.close()

@app.command(help='It displays all the subjects and topics that are available inside the database.')
def display():
    with open("settings.json", "r") as read_file:
        settings = json.load(read_file)
    conn = sqlite3.connect(PATH_TO_DB)
    cursor = conn.cursor()
    result = cursor.execute(f'''
        SELECT rowid,* FROM subject_tracking
    ''')
    table_headers = ['ID','Subject','Topics','Starting Date']
    for elem in range(settings["number_of_repetition"]):
        table_headers.append(f'Revision{elem + 1}')
    table = Table(*table_headers)
    for item in result:
        row_elements = []
        for elem in item:
            row_elements.append(str(elem))
        table.add_row(*row_elements)
        
    console = Console()
    console.print(table)
    conn.close()

@app.command(help='Insert a new subject into the database.')
def add(subject:Annotated[str,Option(prompt=True)],topics:Annotated[str,Option(prompt=True)],start_date:Annotated[str,Option(prompt='Date(format:YYYY-MM-DD)')]):
    with open("settings.json", "r") as read_file:
        settings = json.load(read_file)
    conn = sqlite3.connect(PATH_TO_DB)
    cursor = conn.cursor()
    # dates related to subject
    start_date = date.fromisoformat(start_date)
   
    sql_query_text = f'INSERT INTO subject_tracking VALUES ("{subject}","{topics}","{start_date}"'
    prev_date = start_date
    for item in settings['gaps_between_revisions'].values():
        sql_query_text = sql_query_text + f',"{prev_date + timedelta(days=item)}"'
        prev_date = prev_date + timedelta(days=item)
    sql_query_text = sql_query_text + ')'
    cursor.execute(sql_query_text)
    conn.commit()
    conn.close()
    print(f'{subject} and {topics} added successfully.')

@app.command(help='Initialize the app for the first time and setup the database file.')
def init():
    settings = {}
    if os_path.isfile(PATH_TO_DB):
        print('App has already been initialized.')
        print('-Use different commands to interact with the app')
    else:
        conn = sqlite3.connect(PATH_TO_DB)
        # creating sql query string based on user input
        number_of_repetition = int(input('How many repetition do you want ? '))
        settings['number_of_repetition'] = number_of_repetition
        list_of_gaps_between_revisions = input('How many days of gap do you want between each revision ?\nProvide a space separated list of days(e.g. 3 4 5 7) : ')
        list_of_gaps_between_revisions = list_of_gaps_between_revisions.strip()
        list_of_gaps_between_revisions = list_of_gaps_between_revisions.split()
        list_of_gaps_between_revisions = list(map(lambda x:int(x),list_of_gaps_between_revisions))
        settings['gaps_between_revisions'] = {}
        sql_date_text = ''
        settings['revision_column_name'] = []
        for i in range(0,number_of_repetition):
            
            settings['gaps_between_revisions'][f'_{i+1}_revision_gap'] = list_of_gaps_between_revisions[i]
            settings['revision_column_name'].append(f'_{i+1}_revision') 
            sql_date_text = sql_date_text + f'_{i+1}_revision TEXT'
            if i != number_of_repetition-1:
                sql_date_text = sql_date_text + ','
        
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE subject_tracking(
                       subject TEXT,
                       topics TEXT,
                       start_date TEXT,
                       {sql_date_text}
            )
        ''')
        conn.commit()
        conn.close()
        with open("settings.json", "w") as write_file:
            json.dump(settings, write_file)
        print("App and it's database has been initialized.")


@app.callback()
def main():
    """
    This commandline tool helps you to leverage your 
    learning by using spaced repetition method.\n
    🚀 Add the subject and topics with the start date.\n
    🚀 It will automatically compute the revision dates.\n
    🚀 Shows the subjects that you have to revise based on current date.
    """

if __name__ == '__main__':
    app()