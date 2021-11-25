import urllib.parse
import requests
import simplejson as json
import pandas
import numpy
import math

pandas.set_option("display.max_rows", 500)
pandas.set_option("display.max_columns", 500)
pandas.set_option("display.width", 1000)

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://magiceden.io",
    "Accept-Encoding": "gzip, deflate, br",
    "Host": "api-mainnet.magiceden.io",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://magiceden.io/",
    "Connection": "keep-alive",
}


def GetListings(number_of_listings: int, ashift: int):
    """
    Magic Eden allows for a max of 500 listings upon query. If number_of_listings exceed 500,
    consider the difference as the ashift value. If magnitudes greater than 500*2, chunk fn calls.
    """
    if number_of_listings > 500:
        print(
            f"Exceeding maximum listing query depth. Consider ashifting by {number_of_listings-500}"
        )

    # encoded query is json fmt -
    #
    #       {"$match":{"collectionSymbol":"dapper_ducks"},"$sort":{"createdAt":-1},"$skip":40,"$limit":20}
    #
    query = {
        "$match": {
            "collectionSymbol": "dapper_ducks",
        },
        "$sort": {
            "createdAt": -1,
        },
        "$skip": int(ashift),
        "$limit": int(number_of_listings),
    }
    payload = {
        "q": json.dumps(query).replace(" ", ""),
    }
    response: requests.Response = requests.request(
        "GET",
        f"https://api-mainnet.magiceden.io/rpc/getListedNFTsByQuery?{urllib.parse.urlencode(payload)}",
        headers=headers,
    )
    body = json.loads(response.text)["results"]

    df = pandas.DataFrame(body)

    return df[["owner"]]


def GetNumberOfListings():
    response: requests.Response = requests.request(
        "GET",
        "https://api-mainnet.magiceden.io/rpc/getCollectionEscrowStats/dapper_ducks",
        headers=headers,
    )
    count = json.loads(response.text)["results"]["listedCount"]

    return count


if __name__ == "__main__":

    listings_count = GetNumberOfListings()

    owners = numpy.array([], dtype=object)
    epochs = numpy.array_split(
        numpy.arange(start=0, stop=listings_count), int(math.ceil(listings_count / 500))
    )

    for i, epoch in enumerate(epochs):
        _owners = GetListings(len(epoch), min(epoch))
        owners = numpy.append(owners, _owners)

    owners_listing_count_df = pandas.DataFrame(owners, columns=["owner"]).value_counts().reset_index(name='count')
    print(owners_listing_count_df)
    print("Most duck listed per owner: "+str(owners_listing_count_df['count'].max()))
    print("Total unique owner: "+str(len(owners_listing_count_df)))
    print("Total listed ducks: "+owners_listing_count_df.sum().drop('owner').to_string(index = False))
