# fair-flights

# REQUIREMENTS
- Scrape flight price information from ctrip
- User can specify dates, departing airport/city and destination
- Stores scraped data to a csv file

# TECHNOLOGY
- Selenium for dynamic website scraping
- Beautiful Soup for parsing html

# HOW TO RUN
This is a single file project, currently only able to search one-way flight on ctrip

##Basic usage example
in __main__
- dept_date = datetime.datetime.strptime('2020-04-01' # Your date of departure, ...)
- dept_city = "London"
- dest_city = "Shanghai"
- flex_day_range = 10 # the range of departure dates

from terminal run
'''python ctrip_selenium.py'''

The results will be stored as a csv file under the directory of the program. The program is only tested on Windows now.
To disable headless chrome, comment the chrome_options

# FOOT NOTE
I am hoping that this can be of use to anybody who wants to get home in this extraordinary situation.
This program is NOT to be used for commercial purposes.
Good luck flight hunting!
