from selenium import webdriver
from bs4 import BeautifulSoup
import urllib.request as ulib
from flask_cors import CORS, cross_origin
from flask import Flask, render_template, request, jsonify
import time
import os

if 0:
    #------ Done for running Chrome on Heroku ------
    GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'
    CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = GOOGLE_CHROME_PATH
    #-----------------------------------------------

# import request
app = Flask(__name__) # initialising the flask app with the name 'app'

google_url = 'https://www.google.com'
maxitems_download = 6


def scroll_to_end(webdriver, sleep_between_interactions=1):
    webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(sleep_between_interactions)


def getPageSource(webdriver, urlpage):
    webdriver.get(urlpage)
    page = webdriver.page_source
    return page


def getURLs(webdriver, urlpage, maxitems_download=100, sleeptime=1):
    URLlist_tagobj = []
    len_ = len(URLlist_tagobj)
    while len_ < maxitems_download:
        scroll_to_end(webdriver, sleep_between_interactions=1)
        # get the page source
        page = getPageSource(webdriver, urlpage)
        # parse html through  beautifulsoup, lxml just treats html as text
        soup = BeautifulSoup(page, 'html')
        # get the desired URLs as tag object from bs
        desiredURLs = soup.findAll('img', {'class': 'rg_i Q4LuWd'})  # returns a list of tag beautiful soup objects
        URLlist_tagobj.extend(desiredURLs)
        len_ = len(URLlist_tagobj)

    return desiredURLs

@app.route('/')  # route for redirecting to the home page
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/searchImages', methods=['POST'])  # route for redirecting to the home page
@cross_origin()
def searchImages():
    if request.method == 'POST':
        print("entered post")
        keyword = request.form['keyword'] # assigning the value of the input keyword to the variable keyword
    else:
        print("did not enter post")
    print('printing = ' + keyword)

    wd = webdriver.Chrome(executable_path='chromedriver.exe')
    #wd = webdriver.Chrome(CHROMEDRIVER_PATH)# , chrome_options=chrome_options)
    urlpage = "https://www.google.co.in/search?q=" + keyword + "&source=lnms&tbm=isch"
    URLs_tagobj_bs = getURLs(wd, urlpage, maxitems_download=maxitems_download)
    URLs_tagobj_bs = URLs_tagobj_bs[0:maxitems_download]
    len_tagobj = len(URLs_tagobj_bs)
    print(f'Number of tag objects found: {len_tagobj}')

    # find all unique key for dicts inside list
    keys = []
    for tag in URLs_tagobj_bs:  # iterate over list
        keys.extend(tag.attrs.keys())  # tag is a bs object which can be converted to a dict using .attrs

    print(list(set(keys)))  # this shows that key for image link is either 'src' or 'data-src'

    url_list = []

    for tag in URLs_tagobj_bs:  # iterate over list
        curr_dict = tag.attrs  # tag is a bs object which can be converted to a dict using .attrs
        # extract url of image from dict and append to list
        try:
            url_image = curr_dict['src']
            url_list.append(url_image)
        except KeyError:
            url_image = curr_dict['data-src']
            url_list.append(url_image)
        except:
            print("Key not found,... continuing with next item")
            continue

    # delete if any files are there in static folder
    fname_list = os.listdir('static')
    if len(fname_list) > 0:
        for file in fname_list:
            if not file.endswith('.css'):
                try:
                    os.remove("static" + "\\" + file)
                except:
                    print(f'cannot delete file: {file}')


    # save these files in static folder
    fname_list1 = []
    for i, image_url in enumerate(url_list):
        savefile = os.path.join("static", f'{keyword}_{i:06}.jpg')
        try:
            ulib.urlretrieve(image_url, savefile)
            fname_list1.append(f'{keyword}_{i:06}.jpg') # ShowImage.html itself appends static in the image path
        except:
            print(f"Failed downloading url: {image_url}")

    # render it to showImage.html
    wd.quit()

    return render_template('showImage.html', user_images=fname_list1)



if __name__ == "__main__":
    app.run(debug=True)  # to run on cloud

