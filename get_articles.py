import os
import json

from urllib.error import URLError

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


def mkdir_for_screens_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


if __name__ == "__main__":
    total_articles_list = []

    mkdir_for_screens_if_not_exists("HABR_ARTICLES")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    driver.get("https://habr.com/ru")
    login_button_wait = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tm-header-user-menu__login"))
    )

    login_button = driver.find_element(By.CLASS_NAME, "tm-header-user-menu__login")

    login_button.click()

    email_input = driver.find_element(By.XPATH, "//input[@type='email']")
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    recapcha = driver.find_element(By.ID, "captcha_widget")
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")

    email_input.send_keys("<USER>")
    password_input.send_keys("<PASSWORD>")

    recapcha.click()

    submit_button.click()

    habr_blog_url = "https://habr.com/ru/companies/selectel"

    try:
        driver.get("{}/articles/page1".format(habr_blog_url))
        last_page_group_number_waiter = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tm-pagination__page"))
        )

        last_page_group_number = int(driver.find_elements(By.CLASS_NAME, "tm-pagination__page")[-1].text)

        print("THere are {} pages".format(last_page_group_number))
    except URLError:
        print("There was something wrong with page {}/articles/page1".format(habr_blog_url))

        exit(-1)

    for i in range(86, last_page_group_number):
        current_articles_list = []

        try:

            driver.get("{}/articles/page{}/".format(habr_blog_url, i))

            tm_articles_list = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tm-articles-list__item"))
            )
        except URLError:
            print("There was something wrong with page {}".format(
                "{}/articles/page{}/".format(habr_blog_url, i)
            ))

        try:
            articles = driver.find_elements(By.CLASS_NAME, "tm-articles-list__item")

            print("THere are {} articles".format(len(articles)))
        except NoSuchElementException:
            print("Articles were not found")

            continue

        for j, article in enumerate(articles):
            try:
                title_link = article.find_element(By.CLASS_NAME, "tm-title_h2").find_element(By.CSS_SELECTOR, "a")
                hubs = article.find_elements(By.CLASS_NAME, "tm-publication-hub__link-container")

                hub_list = []
                for hub in hubs:
                    hub_list.append(hub.text.replace("\n", ""))

                article_title = title_link.text
                article_link = title_link.get_attribute("href")

                current_articles_list.append({
                    "article_title": article_title,
                    "article_link": article_link,
                    "hub_list": hub_list
                })

                print("Link: {}. Page: {}; Article: {}".format(article_link, i, j + 1))
            except NoSuchElementException:
                print("Title link was not found")

                continue

        for j, article in enumerate(current_articles_list):
            driver.get("{}comments/".format(article["article_link"]))

            comments_list = []

            try:
                comment_block = driver.find_element(By.CLASS_NAME, "tm-comments__tree")

                comments = comment_block.find_elements(By.CLASS_NAME, value="tm-comment-thread__comment")

                for comment in comments:
                    driver.execute_script("arguments[0].scrollIntoView(true);", comment)

                    comment_text = comment.find_element(
                        By.CLASS_NAME,
                        value="tm-comment__body-content"
                    ).text

                    comment_votes = ""

                    if "НЛО прилетело и опубликовало эту надпись здесь" not in comment_text:
                        try:
                            votes_presence_waiter = WebDriverWait(comment, 30).until(
                                EC.any_of(
                                    EC.presence_of_element_located((
                                        By.CLASS_NAME,
                                        "tm-votes-lever__score.tm-votes-lever__score.tm-votes-lever__score_appearance-comment"
                                    )),
                                    EC.presence_of_element_located((
                                        By.CLASS_NAME,
                                        "tm-votes-meter__value"
                                    ))
                                )
                            )
                            votes_visibility_waiter = WebDriverWait(comment, 30).until(
                                EC.any_of(
                                    EC.visibility_of_element_located((
                                        By.CLASS_NAME,
                                        "tm-votes-lever__score.tm-votes-lever__score.tm-votes-lever__score_appearance-comment"
                                    )),
                                    EC.visibility_of_element_located((
                                        By.CLASS_NAME,
                                        "tm-votes-meter__value"
                                    ))
                                )
                            )

                            try:
                                comment_votes = comment.find_element(
                                    By.CLASS_NAME,
                                    value="tm-comment-footer"
                                ).find_element(
                                    By.CLASS_NAME,
                                    value="tm-votes-lever__score.tm-votes-lever__score.tm-votes-lever__score_appearance-comment"
                                ).text
                            except NoSuchElementException as e:
                                # print(
                                #     "Article {} was having issues with comment votes. Page: {}; Article: {}. Applying alternative selector".format(
                                #         article["article_link"],
                                #         i,
                                #         j + 1
                                # ))
                                try:
                                    comment_votes = comment.find_element(
                                        By.CLASS_NAME,
                                        value="tm-comment-footer"
                                    ).find_element(
                                        By.CLASS_NAME,
                                        value="tm-votes-meter__value"
                                    ).text

                                except NoSuchElementException as e:
                                    comment_votes = 0

                                    print(e)

                                    print(
                                        "Article {} was having issues with comment vote extraction. Page: {}; Article: {}. Comment:\n\n {}".format(
                                            article["article_link"], i, j + 1, comment_text
                                    ))
                        except TimeoutException as e:
                            comment_votes = 0

                            print(e)

                            print(
                                "Article {} was having issues with comment vote extraction. Page: {}; Article: {}. Comment:\n\n {}".format(
                                    article["article_link"], i, j + 1, comment_text
                            ))

                        comment_creation_time = comment.find_element(
                            By.CLASS_NAME, value="tm-comment-thread__comment-link"
                        ).find_element(
                            By.CSS_SELECTOR, value="time"
                        ).get_attribute("datetime")

                        comments_list.append({
                            "comment_text": comment_text,
                            "comment_creation_time": comment_creation_time,
                            "comment_votes": int(comment_votes)
                        })
            except NoSuchElementException:
                print("Article {} was having no comments. Page: {}; Article: {}".format(
                    article["article_link"],
                    i,
                    j + 1
                ))

            article["comments_list"] = comments_list

        with open(os.path.join("HABR_ARTICLES", "articles_list_page_{}.json".format(i)), "w", encoding="utf8") as f:
            json.dump(current_articles_list, f, ensure_ascii=False)
