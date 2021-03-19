import requests
import json
import pandas as pd

query = """
query SearchPackListings($input: SearchPackListingsInput!) {
  searchPackListings(input: $input) {
    data {
      searchSummary {
        data {
          ... on PackListings {
            data {
              id
              price
              title
              remaining
              totalPackCount
              expiryDate
              preorder
              images {
                type
                url
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""
variables = {'input': {'searchInput': {'pagination': {'cursor': "", 'direction': "RIGHT", 'limit': '100'}}}}

url = 'https://api.nbatopshot.com/marketplace/graphql?SearchPackListings'
r = requests.post(url, json={'query': query, 'variables': variables})

json_data = json.loads(r.text)

print(json_data)

df_data = json_data['data']['searchPackListings']['data']['searchSummary']['data']['data']
df = pd.DataFrame(df_data)
print(df)