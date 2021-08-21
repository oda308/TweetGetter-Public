# -*- coding: utf-8 -*-
import tweepy
from flask import Flask, render_template, request, send_from_directory, make_response
import re
import csv
import os
import random

#ツイッター接続用Key
CONSUMER_KEY = ""
CONSUMER_SECRET_KEY = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

#グローバル変数
last_form_settings = {"last_input": ''
                    , "last_more_tweet_mode": ''
                    , "last_media_mode": 'media_mode_off'
                    , "last_mode_option": 'off'
                    , "last_search_mode": 'free_search_mode'}

app = Flask(__name__)

def setRandomHashTag(hash_tag_index, hash_tag_text):
    #ランダムハッシュタグのリストを取得
    with open("random_hash_tag.csv", 'r', encoding = 'utf-8', newline = '') as f:
        temp = csv.reader(f, delimiter=",")
        for row in temp:
            random_hash_tag_list = row
    random_hash_tag_list[int(hash_tag_index)] = hash_tag_text

    #ファイルを上書きモードで書き込み
    with open("random_hash_tag.csv", 'w', encoding = 'utf-8', newline = '') as f:
        temp = csv.writer(f, delimiter=",")
        #出力
        temp.writerow(random_hash_tag_list)

def getRandomHashTag():
    #ファイルからハッシュタグを読み込む
    with open("random_hash_tag.csv", 'r', encoding = 'utf-8', newline = '') as f:
        temp = csv.reader(f, delimiter=",")
        for row in temp:
            random_hash_tag_list = row
        return random_hash_tag_list

def tweetFormatting(text):
    ### 特定の文字列をツイートから削除 ###
    #文中のURLツイート直前の絵文字を削除(対応を再考したい)
    tmp = re.sub(r"(\n\n.http)+", "http", text)
    #文中の"https://t.co/"から始まるURLを削除
    tmp = re.sub(r"(https://t.co/.{10})*", "", tmp)
    #文中の"http://t.co/"から始まるURLを削除
    tmp = re.sub(r"(http://t.co/.{10})*", "", tmp)
    #文末に" "があった場合削除
    tmp = re.sub(r" $", "", tmp)
    #文頭の"RT "を削除
    tmp = re.sub(r"^RT ", "", tmp)
    #文頭の@ユーザー名を削除、マッチがなくなるまで繰り返し処理を行う
    tmp = re.sub(r"^(@.*? )*", "", tmp)
    #改行が2回続いた場合1つにする
    tmp = re.sub(r"(\n\n)+", "\n", tmp)
    #末尾の改行をすべて削除する
    text = re.sub(r"(\n)+$", "", tmp)

    return text

def exportCsv(contents, file_name):
    #既にファイルが存在する場合削除
    if os.path.exists(file_name):
        os.remove(file_name)

    #contentsの要素数分空の二次元配列を作成
    temp = [[] for i in range(len(contents) + 1)]

    #リストの先頭にタグを追加
    temp[0] += ["ツイート", "URL"]

    #イテレータ宣言
    count = 1

    #辞書型オブジェクトをリストに変換
    for content in contents:
        #ツイート本文とメディアURLを取得 /ツイート内の改行文字を削除
        string = ''.join(content["text"].splitlines())
        temp[count] = [string, content["media_url"]]
        count += 1

    #取得したコンテンツをCSVで出力, ユニバーサル改行モードをオフにする
    with open(file_name, 'a+', encoding = 'utf-16', newline = '') as f:
        #全ての改行コードを\nに指定
        writer = csv.writer(f, lineterminator='\n', dialect='excel', delimiter='\t', quoting=csv.QUOTE_ALL)
        #出力
        writer.writerows(temp)

def exportTxt(contents, file_name):

    #既にファイルが存在する場合削除
    if os.path.exists(file_name):
        os.remove(file_name)

    #テンプレート作成
    temp = []

    #テンプレートのリストにコンテンツを入れていく
    for i in range(0, len(contents) - 1):
        temp.append('----------------' + '\n')
        string = ''.join(contents[i]['text'].splitlines())
        temp.append('Tweet : ' + string + '\n')
        temp.append('URL   : ' + contents[i]['media_url'] + '\n')

    #ファイルオープン
    with open(file_name, 'a+', encoding = 'utf-16', newline = '') as f:
        #出力
        f.writelines(temp)


@app.route('/', methods=['GET', 'POST'])
def test():

    ### POST処理 ###
    if (request.method == 'POST'):
        #ランダムハッシュタグを書き換え、設定画面へ遷移
        try:
            setRandomHashTag(request.form['hash_tag_index'], request.form['hash_tag_text'])
            random_hash_tag_list = getRandomHashTag()
            return render_template('random_hash_tag.html', random_hash_tag_list = random_hash_tag_list)
        #ランダムハッシュタグを取得し、設定画面へ遷移
        except:
            random_hash_tag_list = getRandomHashTag()
            return render_template('random_hash_tag.html', random_hash_tag_list = random_hash_tag_list)

    ### GET処理 ###
    else:
        #inputフォームが空だった場合
        if ((request.args.get('input_word') == '') or (request.args.get('input_word') == None)):
            last_form_settings["last_input"] = ''
            last_form_settings["last_media_mode"] = "media_mode_off"
            last_form_settings["last_mode_option"] = "off"
            #inputフォームに何も入力されていなかった場合はリターン
            return render_template('index.html', user_id = '', user_name = '', tweets = '', last_form_settings = last_form_settings)
        #inputフォームからパラメータを取得できた場合
        else:
            last_form_settings["last_input"] = request.args.get('input_word')
            last_form_settings["last_mode_option"] = request.args.get('mode_option')

        last_form_settings["last_more_tweet_mode"] = request.args.get('more_tweet_mode')

        #メディアモード設定
        if request.args.get('search_mode') == "free_search_mode":
            last_form_settings["last_media_mode"] = request.args.get('media_mode')
        #ユーザーID検索時、検索設定が空の場合はメディアモードをオフにする
        else:
            last_form_settings["last_media_mode"] = "media_mode_off"

        #検索モードが空だった場合何もせず、前回の設定を引き継ぐ
        if request.args.get('search_mode') != '' and request.args.get('search_mode') != None:
            last_form_settings["last_search_mode"] = request.args.get('search_mode')

        #空要素を排除したハッシュタグリスト作成のため宣言
        configured_hash_tag_list = []

        #ランダムハッシュタグ設定
        temp_hash_tag_list = getRandomHashTag()
        for row in temp_hash_tag_list:
            #ハッシュタグリストが空でないとき、その要素を配列に加える
            if len(row) != 0:
                configured_hash_tag_list.append(row)

        #SearchModeに応じてツイートの取得数、取得ページ上限を変更
        max_receive_tweet_num = 200 if last_form_settings["last_search_mode"] == 'user_search_mode' else 100
        max_receive_page_num = 50 if last_form_settings["last_search_mode"] == 'user_search_mode' else 15
        #取得ページ下限は決め打ち
        min_receive_page_num = 1

        #MoreTweetMode設定
        ref_page_num = max_receive_page_num if last_form_settings["last_more_tweet_mode"] else min_receive_page_num

        #ツイート本文, 動画のurlを格納する配列を宣言
        #Detail View On設定
        if (last_form_settings["last_mode_option"] == 'detail_view_mode'):
            tweets = [{"tweet_count":0, "tweet_id":'', "time_stamp":'', "retweet":'', "like": '', "text" : '', "media_url": '', "random_hash_tag": ''} for i in range(ref_page_num * max_receive_tweet_num)]
        #Detail View Off設定
        else:
            tweets = [{"tweet_count":0, "tweet_id":'', "text" : '', "media_url": '', "random_hash_tag": ''} for i in range(ref_page_num * max_receive_tweet_num)]

        #各種キー設定
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET_KEY)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

        #tweepy初期化
        tweepy_api = tweepy.API(auth)

        count = 0
        last_id = 0

        #検索キーワードの変更処理 / フリーワード検索時のみ
        if last_form_settings["last_search_mode"] =='free_search_mode':
            #1.リツイート投稿は検索結果から除外する
            search_string = last_form_settings['last_input'] + " exclude:retweets"
            #2.画像/動画を持つツイートのみ表示する場合
            if last_form_settings["last_media_mode"] == "media_mode_media":
                search_string = search_string + " filter:media"
            #動画のみ取得
            elif last_form_settings["last_media_mode"] == "media_mode_videos":
                search_string = search_string + " filter:videos"
            #画像のみ取得
            elif last_form_settings["last_media_mode"] == "media_mode_images":
                search_string = search_string + " filter:images"
            #メディアモードオフ
            else:
                pass

        #特定のユーザーのツイート取得
        for i in range(0, ref_page_num):
            #ツイートの取得
            if last_form_settings["last_search_mode"] =='free_search_mode':
                tweet_container = tweepy_api.search(search_string, count = max_receive_tweet_num, max_id = str(last_id - 1),tweet_mode='extended')
            else:
                tweet_container = tweepy_api.user_timeline(last_form_settings['last_input'], count = max_receive_tweet_num, page = i, tweet_mode='extended')
    
            #最後に取得したツイートIdを格納
            last_id = tweet_container[-1].id

            for tweet in tweet_container:
                #MediaMode On設定
                if (last_form_settings["last_media_mode"] != "media_mode_off"):
                    #埋め込みのメディアの存在確認
                    if (hasattr(tweet, "extended_entities")):
                        if ("media" in tweet.extended_entities):
                            if ("expanded_url" in tweet.extended_entities["media"][0]):
                                #Detail View On設定
                                if (request.args.get('mode_option') == 'detail_view_mode'):
                                    tweets[count]["time_stamp"] = tweet.created_at
                                    tweets[count]["retweet"] = tweet.retweet_count
                                    tweets[count]["like"] = tweet.favorite_count
                                tweets[count]["text"] = tweet.full_text
                                tweets[count]["media_url"] = tweet.extended_entities["media"][0]["expanded_url"]
                                tweets[count]["tweet_id"] = tweet.id
                #MediaMode Off設定
                else:
                    #Detail View On設定
                    if (last_form_settings["last_mode_option"] == 'detail_view_mode'):
                        tweets[count]["time_stamp"] = tweet.created_at
                        tweets[count]["retweet"] = tweet.retweet_count
                        tweets[count]["like"] = tweet.favorite_count
                    tweets[count]["text"] = tweet.full_text
                    #埋め込みのメディアの存在確認
                    if (hasattr(tweet, "extended_entities")):
                        if ("media" in tweet.extended_entities):
                            if ("expanded_url" in tweet.extended_entities["media"][0]):
                                tweets[count]["media_url"] = tweet.extended_entities["media"][0]["expanded_url"]
                                tweets[count]["tweet_id"] = tweet.id
                    else:
                        tweets[count]["media_url"] = ''
                #Detail View Off設定
                if (last_form_settings["last_mode_option"] != 'detail_view_mode'):
                    tweets[count]["text"] = tweetFormatting(tweets[count]["text"])
                    #blind_url_mode設定(詳細表示Off時のみ設定)
                    if (last_form_settings["last_mode_option"] == 'blind_url_mode'):
                        #文中にURLが存在していた場合、そのツイートを非表示にする
                        if tweets[count]["text"].find("http") != -1:
                            tweets[count]["text"] = ''
                #ランダムハッシュタグの割り当て
                list_length = len(configured_hash_tag_list)
                tweets[count]["random_hash_tag"] = configured_hash_tag_list[random.randrange(list_length)]
                #各ツイートに番号を割り振り
                tweets[count]["tweet_count"] = count
                count += 1

        #CSVエクスポート処理
        if (request.args.get('button_cmd') == "CSVダウンロード"):
            exportCsv(tweets, 'tweets.csv')
            #ファイルのダウンロードを開始させる
            return send_from_directory('./', 'tweets.csv', as_attachment = True)
        #TEXTエクスポート処理
        elif (request.args.get('button_cmd') == "TEXTダウンロード"):
            exportTxt(tweets, 'tweets.txt')
            #ファイルのダウンロードを開始させる
            return send_from_directory('./', 'tweets.txt', as_attachment = True)
        #エクスポートが必要ない場合は通常処理
        else:
            return render_template('index.html', user_id = tweet.user._json['screen_name']
                                            , user_name = tweet.user._json['name']
                                            , tweets = tweets
                                            , last_form_settings = last_form_settings)

if __name__ == "__main__":
    app.run()