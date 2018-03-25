from lxml import html, etree
from lxml.etree import XPath
import requests
import re
import json
import csv
import sys
import time
import numbers
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures


def html_parse_tree(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree

def xpath_parse(tree, xpath):
    result = tree.xpath(xpath)
    return result

def regex_strip_string(string):
    string = re.sub('\n', '', string).strip()
    string = re.sub('\r', '', string).strip()
    string = re.sub('\t', '', string).strip()
    return string

def regex_strip_array(array):
    for i in range(0, len(array)):
        array[i] = regex_strip_string(array[i]).strip()
    return array

def array2csv(array, filename):
    csv_array = array
    csv_out = open(filename + ".csv", 'w')
    mywriter = csv.writer(csv_out)
    # for row in csv_array:
    #   mywriter.writerow(row)
    mywriter.writerows(csv_array)
    csv_out.close()

def read_csv(array, filename):
    with open(filename, 'rb') as input_file:
        foo = csv.reader(input_file)
        for row in foo:
            array.append(row)
    return array

def format_spacing(max_spacing, variable):
    spacing_count = max_spacing - len(variable)
    output = ''
    for i in range(0, spacing_count):
        output += ' '
    return output

def fraction_stats(string):
    string = string.replace('(', '')
    string = string.replace(')', '')
    return string.split('/')

def tournaments(year):
    # Setup
    year_url = "http://www.atpworldtour.com/en/scores/results-archive?year=" + year
    url_prefix = "http://www.atpworldtour.com"

    # HTML tree
    year_tree = html_parse_tree(year_url)

    # XPaths
    tourney_title_xpath = "//span[contains(@class, 'tourney-title')]/text()"
    tourney_title_parsed = xpath_parse(year_tree, tourney_title_xpath)
    tourney_title_cleaned = regex_strip_array(tourney_title_parsed)

    tourney_count = len(tourney_title_cleaned)

    tourney_dates_xpath = "//span[contains(@class, 'tourney-dates')]/text()"
    tourney_dates_parsed = xpath_parse(year_tree, tourney_dates_xpath)
    tourney_dates_cleaned = regex_strip_array(tourney_dates_parsed)

    tourney_singles_draw_xpath = "//div[contains(., 'SGL')]/a[1]/span/text()"
    tourney_singles_draw_parsed = xpath_parse(year_tree, tourney_singles_draw_xpath)
    tourney_singles_draw_cleaned = regex_strip_array(tourney_singles_draw_parsed)

    tourney_doubles_draw_xpath = "//div[contains(., 'DBL')]/a[1]/span/text()"
    tourney_doubles_draw_parsed = xpath_parse(year_tree, tourney_doubles_draw_xpath)
    tourney_doubles_draw_cleaned = regex_strip_array(tourney_doubles_draw_parsed)

    tourney_conditions_xpath = "//div[contains(., 'Outdoor') or contains(., 'Indoor')]/text()[normalize-space()]"
    tourney_conditions_parsed = xpath_parse(year_tree, tourney_conditions_xpath)
    tourney_conditions_cleaned = regex_strip_array(tourney_conditions_parsed)

    tourney_surface_xpath = "//div[contains(., 'Outdoor') or contains(., 'Indoor')]/span/text()[normalize-space()]"
    tourney_surface_parsed = xpath_parse(year_tree, tourney_surface_xpath)
    tourney_surface_cleaned = regex_strip_array(tourney_surface_parsed)

    tourney_fin_commit_xpath = "//td[contains(@class, 'fin-commit')]/div/div/span/text()"
    tourney_fin_commit_parsed = xpath_parse(year_tree, tourney_fin_commit_xpath)
    tourney_fin_commit_cleaned = regex_strip_array(tourney_fin_commit_parsed)    

    output = []
    for i in range(0, tourney_count):
        tourney_order = i + 1

        # Assign variables
        tourney_name = tourney_title_cleaned[i]
        tourney_dates = tourney_dates_cleaned[i]  

        try:
            tourney_conditions = tourney_conditions_cleaned[i].strip()
            tourney_surface = tourney_surface_cleaned[i]
        except Exception:
            tourney_conditions = ''
            tourney_surface = ''

        if len(tourney_fin_commit_cleaned[i]) > 0:
            tourney_fin_commit = tourney_fin_commit_cleaned[i]
        else:
            tourney_fin_commit = ''

        # Tourney URL's
        tourney_details_url_xpath = "//tr[contains(@class, 'tourney-result')][" + str(i + 1) + "]/td[8]/a/@href"
        tourney_details_url_parsed = xpath_parse(year_tree, tourney_details_url_xpath)

        if len(tourney_details_url_parsed) > 0:
            tourney_url_suffix = tourney_details_url_parsed[0]
            tourney_url_split = tourney_url_suffix.split('/')
            tourney_slug = tourney_url_split[4]
            tourney_id = tourney_url_split[5]
        else:
            tourney_url_suffix = ''
            tourney_slug = ''
            tourney_id = ''    


        tourney_year_id = str(year) + '-' + tourney_id
        
        # Store data
        if tourney_url_suffix != '':
            newoutput = np.array([[year, tourney_order, tourney_name, tourney_dates, tourney_conditions, tourney_surface, tourney_url_suffix]])

            if len(output) == 0:
                output = newoutput
            else:
                output = np.concatenate((output, newoutput))

    # Output data
    return output

def matches(base_url, match_url, tourney_id):
    tourney_url = base_url + match_url
    
    # HTML tree
    tourney_tree = html_parse_tree(tourney_url)

    good_html = etree.tostring(tourney_tree, pretty_print=True).strip()
    your_tree = etree.fromstring(good_html)
    matches_xpath = XPath("//table[contains(@class, 'day-table')]//tbody/tr") 
    
    player1_url_xpath = XPath("td[contains(@class, 'day-table-name')][1]/a/@href")
    player1_name_xpath = XPath("td[contains(@class, 'day-table-name')][1]/a/text()")
    player1_seed_xpath = XPath("td[contains(@class, 'day-table-seed')][1]/span/text()")
    
    player2_url_xpath = XPath("td[contains(@class, 'day-table-name')][2]/a/@href")
    player2_name_xpath = XPath("td[contains(@class, 'day-table-name')][2]/a/text()")
    player2_seed_xpath = XPath("td[contains(@class, 'day-table-seed')][2]/span/text()")
    
    result_url_xpath = XPath("td[contains(@class, 'day-table-score')]/a/@href")
    
    output = []
    for match in matches_xpath(your_tree):
        player1_name = player1_name_xpath(match)[0]
        player1_url = player1_url_xpath(match)[0]
        player1_id = player1_url.split('/')[3]
        seed1 = regex_strip_array(player1_seed_xpath(match))
        if len(seed1) > 0:
            player1_seed = seed1[0].replace('(', '').replace(')', '')
        else:
            player1_seed = ""
            
        player2_name = player2_name_xpath(match)[0]
        player2_url = player2_url_xpath(match)[0]       
        player2_id = player2_url.split('/')[3]
        seed2 = regex_strip_array(player2_seed_xpath(match))
        if len(seed2) > 0:
            player2_seed = seed2[0].replace('(', '').replace(')', '')
        else:
            player2_seed = ""
            
        result_url = ""
        result = result_url_xpath(match)
        if len(result) > 0:
            result_url = result[0]
            match_id = result_url.split('/')[5]

            newoutput = np.array([[tourney_id, match_id, player1_id, player1_url, player1_name, player1_seed, 
                                                         player2_id, player2_url, player2_name, player2_seed, result_url]])
            if len(output) == 0:
                output = newoutput
            else:
                output = np.concatenate((output, newoutput))

    return output

def players(base_url, player_urls):
    
    for player_url in player_urls:
        winloss_tree = html_parse_tree(base_url + player_url + "/fedex-atp-win-loss/")
        good_html = etree.tostring(winloss_tree, pretty_print=True).strip()
        winloss_tree = etree.fromstring(good_html)       
        
        summary_xpath = XPath("//div[contains(@class, 'inner-wrap')]/table/tr[1]")
        age_xpath = XPath("//td/div[contains(@class, 'wrap')]/div[contains(@class, 'table-big-value')]/text()")
        dob_xpath = XPath("//span[contains(@class, 'table-birthday-wrapper')]/span[contains(@class, 'table-birthday')]/text()")
        kgs_xpath = XPath("//span[contains(@class, 'table-weight-kg-wrapper')]/text()")
        cms_xpath = XPath("//span[contains(@class, 'table-height-cm-wrapper')]/text()")
        
        for summary in summary_xpath(winloss_tree):
            age = regex_strip_array(age_xpath(summary))[0]
            print("AGE:" + age)
            dob = regex_strip_array(dob_xpath(summary))[0].replace('(', '').replace(')', '')
            print("DOB:" + dob)
            kgs = regex_strip_array(kgs_xpath(summary))[0].replace('(', '').replace(')', '')
            print("Kgs:" + kgs)
            cms = regex_strip_array(cms_xpath(summary))[0].replace('(', '').replace(')', '')
            print("Cms:" + cms)
    
    output = []

    return output

def scrape_tourney(tourney_url_suffix):
    url_prefix = "http://www.atpworldtour.com"
    tourney_url = url_prefix + tourney_url_suffix

    url_split = tourney_url.split("/")
    tourney_slug = url_split[6]
    tourney_year = url_split[8]
    tourney_id = url_split[7]

    # Tourney tree
    tourney_tree = html_parse_tree(tourney_url)     

    tourney_round_name_xpath = "//table[contains(@class, 'day-table')]/thead/tr/th/text()"
    tourney_round_name_parsed = xpath_parse(tourney_tree, tourney_round_name_xpath)
    tourney_round_count = len(tourney_round_name_parsed)

    match_urls = []
    match_data = []
    # Iterate through each round    
    for i in range(0, tourney_round_count):
        round_order = i + 1

        tourney_round_name = tourney_round_name_parsed[i]

        #round_match_count_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr/td[contains(@class, 'day-table-score')]/a/@href"
        round_match_count_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr/td[contains(@class, 'day-table-name')][1]/a/text()"
        round_match_count_parsed = xpath_parse(tourney_tree, round_match_count_xpath)
        round_match_count = len(round_match_count_parsed)

        # Iterate through each match
        for j in range(0, round_match_count):
            match_order = j + 1

            # Winner
            winner_name_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-name')][1]/a/text()"
            winner_name_parsed = xpath_parse(tourney_tree, winner_name_xpath)

            winner_url_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-name')][1]/a/@href"
            winner_url_parsed = xpath_parse(tourney_tree, winner_url_xpath)

            winner_name = winner_name_parsed[0].encode('utf-8')
            winner_url = winner_url_parsed[0]
            winner_url_split = winner_url.split('/')
            winner_slug = winner_url_split[3]
            winner_player_id = winner_url_split[4]            

            # Loser
            loser_name_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-name')][2]/a/text()"
            loser_name_parsed = xpath_parse(tourney_tree, loser_name_xpath)

            loser_url_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i +1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-name')][2]/a/@href"
            loser_url_parsed = xpath_parse(tourney_tree, loser_url_xpath)

            try:
                loser_name = loser_name_parsed[0].encode('utf-8')
                loser_url = loser_url_parsed[0]
                loser_url
                loser_url_split = loser_url.split('/')
                loser_slug = loser_url_split[3]
                loser_player_id = loser_url_split[4]
            except Exception:
                loser_name = ''
                loser_url = ''
                loser_slug = ''
                loser_player_id = ''

            # Seeds
            winner_seed_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-seed')][1]/span/text()"
            winner_seed_parsed = xpath_parse(tourney_tree, winner_seed_xpath)
            winner_seed_cleaned = regex_strip_array(winner_seed_parsed)
            if len(winner_seed_cleaned) > 0:
                winner_seed = winner_seed_cleaned[0]
            else:
                winner_seed = ''
            winner_seed = winner_seed.replace('(', '')
            winner_seed = winner_seed.replace(')', '')
            
            loser_seed_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-seed')][2]/span/text()"        
            loser_seed_parsed = xpath_parse(tourney_tree, loser_seed_xpath)
            loser_seed_cleaned = regex_strip_array(loser_seed_parsed)
            if len(loser_seed_cleaned) > 0:
                loser_seed = loser_seed_cleaned[0]
            else:
                loser_seed = ''
            loser_seed = loser_seed.replace('(', '')
            loser_seed = loser_seed.replace(')', '')        

            # Match score
            match_score_text_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-score')]/a/node()"
            match_score_text_parsed = xpath_parse(tourney_tree, match_score_text_xpath)

            if len(match_score_text_parsed) > 0:

                # Tiebreaks
                tiebreaks_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-score')]/a/sup/text()"
                tiebreaks_parsed = xpath_parse(tourney_tree, tiebreaks_xpath)

                # Fixing tiebreak problem
                tiebreak_counter = 0
                match_score_cleaned = []
                tiebreak_score_cleaned = []
                for element in match_score_text_parsed:
                    if len(element) > 0:
                        match_score_cleaned.append(regex_strip_string(element))
                        tiebreak_score_cleaned.append(regex_strip_string(element))
                    else:
                        match_score_cleaned.append("TIEBREAK")
                        tiebreak_score_cleaned.append("[" + tiebreaks_parsed[tiebreak_counter] + "]")
                        tiebreak_counter += 1

                # Finalize match scores
                concat_match_score = ""
                element_count = len(match_score_cleaned)
                for k in range(0,  element_count - 1):
                    concat_match_score += match_score_cleaned[k] + "::"
                concat_match_score += match_score_cleaned[element_count - 1]

                fix_concat_match_score = concat_match_score.replace("::TIEBREAK::", " ")
                match_score = fix_concat_match_score.split('::')
                
                # Finalize tiebreak scores
                concat_tiebreak_score = ""
                tiebreak_element_count = len(tiebreak_score_cleaned)
                for k in range(0, tiebreak_element_count - 1):
                    concat_tiebreak_score += tiebreak_score_cleaned[k] + "::"
                concat_tiebreak_score += tiebreak_score_cleaned[element_count -1]

                fix_concat_tiebreak_score = concat_tiebreak_score.replace("::[", "(")
                fix_concat_tiebreak_score = fix_concat_tiebreak_score.replace("]::", ") ")    
                tiebreak_score = fix_concat_tiebreak_score.split('::')

                match_score = match_score[0].strip()
                match_score_tiebreaks = tiebreak_score[0].strip()

                winner_sets_won = 0
                loser_sets_won = 0
                winner_games_won = 0
                loser_games_won = 0
                winner_tiebreaks_won = 0
                loser_tiebreaks_won = 0
                match_score_split = match_score.split(' ')

                for sets in match_score_split:
                    if len(sets) == 2:
                        if sets[0] > sets[1]:
                            winner_sets_won += 1
                            winner_games_won += int(sets[0])
                            loser_games_won += int(sets[1])
                            if sets == '76': winner_tiebreaks_won += 1

                        elif sets[0] < sets[1]:
                            loser_sets_won += 1
                            winner_games_won += int(sets[0])
                            loser_games_won += int(sets[1])
                            if sets == '67': loser_tiebreaks_won += 1

                    elif len(sets) == 3:
                        if sets == '810':
                            loser_sets_won += 1
                            loser_games_won += 10
                            winner_games_won += 8
                        elif sets == '108':
                            winner_sets_won += 1
                            winner_games_won += 10
                            loser_games_won += 8
                        elif sets == '911':
                            loser_sets_won += 1
                            loser_games_won += 11
                            winner_games_won += 9
                        elif sets == '119':
                            winner_sets_won += 1
                            winner_games_won += 11
                            loser_games_won += 9

                    elif len(sets) == 4 and sets.isdigit() == True:
                        if sets[0:1] > sets[2:3]:
                            winner_sets_won += 1
                            winner_games_won += int(sets[0:1])
                            loser_games_won += int(sets[2:3])
                        elif sets[2:3] > sets[0:1]:
                            loser_sets_won += 1
                            winner_games_won += int(sets[0:1])
                            loser_games_won += int(sets[2:3])

                # Match id
                match_id = tourney_year + "-" + tourney_id + "-" + winner_player_id + "-" + loser_player_id
                                        
                # Match stats URL
                match_stats_url_xpath = tourney_match_count_xpath = "//table[contains(@class, 'day-table')]/tbody[" + str(i + 1) + "]/tr[" + str(j + 1) + "]/td[contains(@class, 'day-table-score')]/a/@href"
                match_stats_url_parsed = xpath_parse(tourney_tree, match_stats_url_xpath)
                match_stats_url_cleaned = []
                for element in match_stats_url_parsed:
                    if len(element) > 0:
                        match_stats_url_cleaned.append(regex_strip_string(element))
                    else:
                        match_stats_url_cleaned.append("TIEBREAK")
                
                if len(match_stats_url_cleaned) > 0:
                    match_stats_url_suffix = match_stats_url_cleaned[0]
                    match_stats_url_suffix_split = match_stats_url_suffix.split('/')
                    #tourney_long_slug = match_stats_url_suffix_split[3]
                    #tourney_match_id = match_stats_url_split[10]
                    match_urls.append(match_stats_url_suffix)
                else:
                    match_stats_url_suffix = ''
                    tourney_long_slug = ''

                # Store data
                match_data.append([tourney_round_name, round_order, match_order, winner_name, winner_player_id, winner_slug, loser_name, loser_player_id, loser_slug, winner_seed, loser_seed, match_score_tiebreaks, winner_sets_won, loser_sets_won, winner_games_won, loser_games_won, winner_tiebreaks_won, loser_tiebreaks_won, match_id, match_stats_url_suffix])
                #time.sleep(.100)       

    output = [match_data, match_urls]
    return output

def scrape_match_stats(match_url_suffix):
    url_prefix = "http://www.atpworldtour.com"
    match_stats_url = url_prefix + match_url_suffix

    # Match tree
    match_tree = html_parse_tree(match_stats_url)

    # Match time
    try:
        match_time_xpath = "//td[contains(@class, 'time')]/text()"
        match_time_parsed = xpath_parse(match_tree, match_time_xpath)
        match_time_cleaned = regex_strip_array(match_time_parsed)
        match_time = match_time_cleaned[0].replace("Time: ", "")
        match_time_split = match_time.split(":")            
        match_time_hours = int(match_time_split[0])
        match_time_minutes = int(match_time_split[1])
        match_duration = 60*match_time_hours + match_time_minutes                                        
    except Exception:
        match_time = ""
        match_duration = ""      

    match_year = match_url_suffix.split('/')[3]
    tourney_id = match_url_suffix.split('/')[4]        

    winner_slug_xpath = "//div[@class='player-left-name']/a/@href"
    winner_slug_parsed = xpath_parse(match_tree, winner_slug_xpath)
    winner_slug = winner_slug_parsed[0].split('/')[4]

    try:
        loser_slug_xpath = "//div[@class='player-right-name']/a/@href"
        loser_slug_parsed = xpath_parse(match_tree, loser_slug_xpath)
        loser_slug = loser_slug_parsed[0].split('/')[4]
    except Exception:
        loser_slug = ''

    match_id = match_year + '-' + tourney_id + '-' + winner_slug + '-' + loser_slug

    # Match stats
    try:
        winner_stats_xpath = "//td[@class='match-stats-number-left']/span/text()"
        winner_stats_parsed = xpath_parse(match_tree, winner_stats_xpath)
        winner_stats_cleaned = regex_strip_array(winner_stats_parsed)
        
        loser_stats_xpath = "//td[@class='match-stats-number-right']/span/text()"
        loser_stats_parsed = xpath_parse(match_tree, loser_stats_xpath)
        loser_stats_cleaned = regex_strip_array(loser_stats_parsed)

        # Winner stats
        winner_aces = int(winner_stats_cleaned[2])
        winner_double_faults = int(winner_stats_cleaned[3])

        winner_first_serves_in = int(fraction_stats(winner_stats_cleaned[5])[0])
        winner_first_serves_total = int(fraction_stats(winner_stats_cleaned[5])[1])

        winner_first_serve_points_won = int(fraction_stats(winner_stats_cleaned[7])[0])
        winner_first_serve_points_total = int(fraction_stats(winner_stats_cleaned[7])[1])

        winner_second_serve_points_won = int(fraction_stats(winner_stats_cleaned[9])[0])
        winner_second_serve_points_total = int(fraction_stats(winner_stats_cleaned[9])[1])

        winner_break_points_saved = int(fraction_stats(winner_stats_cleaned[11])[0])
        winner_break_points_serve_total = int(fraction_stats(winner_stats_cleaned[11])[1])

        winner_service_points_won = int(fraction_stats(winner_stats_cleaned[23])[0])
        winner_service_points_total = int(fraction_stats(winner_stats_cleaned[23])[1])

        winner_first_serve_return_won = int(fraction_stats(winner_stats_cleaned[16])[0])
        winner_first_serve_return_total = int(fraction_stats(winner_stats_cleaned[16])[1])

        winner_second_serve_return_won = int(fraction_stats(winner_stats_cleaned[18])[0])
        winner_second_serve_return_total = int(fraction_stats(winner_stats_cleaned[18])[1])

        winner_break_points_converted = int(fraction_stats(winner_stats_cleaned[20])[0])
        winner_break_points_return_total = int(fraction_stats(winner_stats_cleaned[20])[1])

        winner_service_games_played = int(winner_stats_cleaned[12])
        winner_return_games_played = int(winner_stats_cleaned[21])

        winner_return_points_won = int(fraction_stats(winner_stats_cleaned[25])[0])
        winner_return_points_total = int(fraction_stats(winner_stats_cleaned[25])[1])

        winner_total_points_won = int(fraction_stats(winner_stats_cleaned[27])[0])
        winner_total_points_total = int(fraction_stats(winner_stats_cleaned[27])[1])

        # Loser stats
        loser_aces = int(loser_stats_cleaned[2])
        loser_double_faults = int(loser_stats_cleaned[3])

        loser_first_serves_in = int(fraction_stats(loser_stats_cleaned[5])[0])
        loser_first_serves_total = int(fraction_stats(loser_stats_cleaned[5])[1])

        loser_first_serve_points_won = int(fraction_stats(loser_stats_cleaned[7])[0])
        loser_first_serve_points_total = int(fraction_stats(loser_stats_cleaned[7])[1])

        loser_second_serve_points_won = int(fraction_stats(loser_stats_cleaned[9])[0])
        loser_second_serve_points_total = int(fraction_stats(loser_stats_cleaned[9])[1])

        loser_break_points_saved = int(fraction_stats(loser_stats_cleaned[11])[0])
        loser_break_points_serve_total = int(fraction_stats(loser_stats_cleaned[11])[1])

        loser_service_points_won = int(fraction_stats(loser_stats_cleaned[23])[0])
        loser_service_points_total = int(fraction_stats(loser_stats_cleaned[23])[1])

        loser_first_serve_return_won = int(fraction_stats(loser_stats_cleaned[16])[0])
        loser_first_serve_return_total = int(fraction_stats(loser_stats_cleaned[16])[1])

        loser_second_serve_return_won = int(fraction_stats(loser_stats_cleaned[18])[0])
        loser_second_serve_return_total = int(fraction_stats(loser_stats_cleaned[18])[1])

        loser_break_points_converted = int(fraction_stats(loser_stats_cleaned[20])[0])
        loser_break_points_return_total = int(fraction_stats(loser_stats_cleaned[20])[1])

        loser_service_games_played = int(loser_stats_cleaned[12])
        loser_return_games_played = int(loser_stats_cleaned[21])

        loser_return_points_won = int(fraction_stats(loser_stats_cleaned[25])[0])
        loser_return_points_total = int(fraction_stats(loser_stats_cleaned[25])[1])

        loser_total_points_won = int(fraction_stats(loser_stats_cleaned[27])[0])
        loser_total_points_total = int(fraction_stats(loser_stats_cleaned[27])[1])

    except Exception:
        winner_aces = ''
        winner_double_faults = ''
        winner_first_serves_in = ''
        winner_first_serves_total = ''
        winner_first_serve_points_won = ''
        winner_first_serve_points_total = ''
        winner_second_serve_points_won = ''
        winner_second_serve_points_total = ''
        winner_break_points_saved = ''
        winner_break_points_serve_total = ''
        winner_service_points_won = ''
        winner_service_points_total = ''
        winner_first_serve_return_won = ''
        winner_first_serve_return_total = ''
        winner_second_serve_return_won = ''
        winner_second_serve_return_total = ''
        winner_break_points_converted = ''
        winner_break_points_return_total = ''
        winner_service_games_played = ''
        winner_return_games_played = ''
        winner_return_points_won = ''
        winner_return_points_total = ''
        winner_total_points_won = ''
        winner_total_points_total = ''

        loser_aces = ''
        loser_double_faults = ''
        loser_first_serves_in = ''
        loser_first_serves_total = ''
        loser_first_serve_points_won = ''
        loser_first_serve_points_total = ''
        loser_second_serve_points_won = ''
        loser_second_serve_points_total = ''
        loser_break_points_saved = ''
        loser_break_points_serve_total = ''
        loser_service_points_won = ''
        loser_service_points_total = ''
        loser_first_serve_return_won = ''
        loser_first_serve_return_total = ''
        loser_second_serve_return_won = ''
        loser_second_serve_return_total = ''
        loser_break_points_converted = ''
        loser_break_points_return_total = ''
        loser_service_games_played = ''
        loser_return_games_played = ''
        loser_return_points_won = ''
        loser_return_points_total = ''
        loser_total_points_won = ''
        loser_total_points_total = ''        

    # Store data
    output = [match_id, match_url_suffix, match_time, match_duration, winner_aces, winner_double_faults, winner_first_serves_in, winner_first_serves_total, winner_first_serve_points_won, winner_first_serve_points_total, winner_second_serve_points_won, winner_second_serve_points_total, winner_break_points_saved, winner_break_points_serve_total, winner_service_points_won, winner_service_points_total, winner_first_serve_return_won, winner_first_serve_return_total, winner_second_serve_return_won, winner_second_serve_return_total, winner_break_points_converted, winner_break_points_return_total, winner_service_games_played, winner_return_games_played, winner_return_points_won, winner_return_points_total, winner_total_points_won, winner_total_points_total, loser_aces, loser_double_faults, loser_first_serves_in, loser_first_serves_total, loser_first_serve_points_won, loser_first_serve_points_total, loser_second_serve_points_won, loser_second_serve_points_total, loser_break_points_saved, loser_break_points_serve_total, loser_service_points_won, loser_service_points_total, loser_first_serve_return_won, loser_first_serve_return_total, loser_second_serve_return_won, loser_second_serve_return_total, loser_break_points_converted, loser_break_points_return_total, loser_service_games_played, loser_return_games_played, loser_return_points_won, loser_return_points_total, loser_total_points_won, loser_total_points_total]
    return output

def synchronous(url_array, parsing_function, tourney_index, tourney_slug):
    results = []
    match_counter = 0
    for match_url in url_array:
        scrape_match_stats_output = [tourney_index]
        scrape_match_stats_output += parsing_function(match_url)
        results.append(scrape_match_stats_output)

        # Output
        match_counter += 1
        current_count = str(match_counter)
        total_matches = len(url_array)
        percent_completed = '{:.0%}'.format(match_counter/float(total_matches))
        spacing1 = format_spacing(5, tourney_index)
        spacing2 = format_spacing(15, tourney_slug)
        sys.stdout.write('\r' + tourney_index + spacing1 + '    ' + tourney_slug + spacing2 + '    ' + current_count + "/" + str(total_matches) + " (" + str(percent_completed) + ")")
        sys.stdout.flush()

        # Pause to prevent timeouts
        #time.sleep(1)         
    print("")
    return results

def asynchronous(url_array, parsing_function, tourney_index, tourney_slug):
    URLS = url_array

    with ProcessPoolExecutor(max_workers = 4) as executor:
        future_results = {executor.submit(parsing_function, url): url for url in URLS}

        results = []
        match_counter = 0
        for future in concurrent.futures.as_completed(future_results):

            scrape_match_stats_output = [tourney_index]
            scrape_match_stats_output += future.result()
            results.append(scrape_match_stats_output)

            # Output
            match_counter += 1
            current_count = str(match_counter)
            total_matches = len(url_array)
            percent_completed = '{:.0%}'.format(match_counter/float(total_matches))
            spacing1 = format_spacing(5, tourney_index)
            spacing2 = format_spacing(15, tourney_slug)
            sys.stdout.write('\r' + tourney_index + spacing1 + '    ' + tourney_slug + spacing2 + '    ' + current_count + "/" + str(total_matches) + " (" + str(percent_completed) + ")")
            sys.stdout.flush()            

            # Pause to prevent timeouts
            #time.sleep(1) 

    print("")
    return results