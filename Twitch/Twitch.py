import aiohttp
import requests as r



class TwitchAPI:
    """
    Twitch API wrapper class
    
    Attributes
    ----------
    client_id : str
        Twitch API client ID
    client_secret : str
        Twitch API client secret
    
    Methods
    -------
    get_twitch_app_access_token()
        Get access token for Twitch API
    check_access_token()
        Check if access token is valid
    get_game_id(game_name)
        Get game ID for game name
    get_category_stats(category_id)
        Get stats for category ID
    get_top_streamers(category_id)
        Get top streamers for category ID
    get_api_points()
        Get API points remaining
    get_category_image(category_id)
        Get image for category ID
    """
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_twitch_app_access_token()
        self.streams = "https://api.twitch.tv/helix/streams"
        self.users = "https://api.twitch.tv/helix/users"
        self.top = "https://api.twitch.tv/helix/games/top"


    def get_twitch_app_access_token(self):
        """
        Get access token for Twitch API
        
        Returns
        -------
        str
            Access token
        
        Returns
        -------
        int
            Status code
        """
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        response = r.post(url, params=params)

        if response.status_code == 200:
            access_token = response.json()["access_token"]
            return access_token
        else:
            return response.status_code


    async def check_access_token(self):
        """
        Check if access token is valid
        
        Returns
        -------
        bool
            True if valid, False if not
        """
        headers = {"Authorization": f"OAuth {self.access_token}"}
        url = "https://id.twitch.tv/oauth2/validate"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return True
                else:
                    return False
    

    async def get_game_id(self, game_name):
        """
        Get game ID for game name
        
        Parameters
        ----------
        game_name : str
            Game name
        
        Returns
        -------
        str
            Game ID
        
        Returns
        -------
        str
            Error message
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Client-ID": self.client_id
        }
        url = f"https://api.twitch.tv/helix/games?name={game_name}"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data["data"]) > 0:
                        game_id = data["data"][0]["id"]
                        return game_id
                    else:
                        return f"No game found with name {game_name}"
                else:
                    return f"Failed to get game ID for {game_name} with status code {response.status}"


    async def get_category_stats(self, category_id):
        """
        Get stats for category ID
        
        Parameters
        ----------
        category_id : str
            Category ID
        
        Returns
        -------
        dict
            Stats for category ID. Keys: viewer_count, stream_count, average_viewer_count, category_rank
        """
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"game_id": category_id}
    
        total_viewer_count = 0
        total_stream_count = 0
        average_viewer_count = 0
        category_rank = 0
    
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.streams, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
    
                for stream in data["data"]:
                    total_viewer_count += stream["viewer_count"]
                    total_stream_count += 1
    
                while "cursor" in data.get("pagination", {}):
                    params["after"] = data["pagination"]["cursor"]
                    async with session.get(self.streams, params=params) as response:
                        data = await response.json()
                        for stream in data["data"]:
                            total_viewer_count += stream["viewer_count"]
                            total_stream_count += 1
    
        if total_stream_count > 0:
            average_viewer_count = total_viewer_count / total_stream_count
    
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.top, params={"first": "100"}) as response:
                if response.status != 200:
                    return response.status
                data = await response.json()
    
                for i, category in enumerate(data["data"]):
                    if category["id"] == category_id:
                        category_rank = i + 1
                        break
    
        response_obj = {
            "viewer_count": total_viewer_count,
            "stream_count": total_stream_count,
            "average_viewer_count": average_viewer_count,
            "category_rank": category_rank
        }
    
        return response_obj


    async def get_top_streamers(self, category_id):
        """
        Get top streamers for category ID
        
        Parameters
        ----------
        category_id : str
            Category ID
        
        Returns
        -------
        dict
            Top streamers for category ID. Keys: streamer_name, viewer_count, follower_count, stream_title, started_at, language, thumbnail_url, link
        """
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"game_id": category_id, "first": "4"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.streams, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    top_streamers = {}
                    for i, stream in enumerate(data["data"]):
                        streamer_name = stream["user_name"]
                        viewer_count = stream["viewer_count"]
                        follower_count = stream["user_id"]
                        stream_title = stream["title"]
                        started_at = stream["started_at"]
                        language = stream["language"]
                        thumbnail_url = stream["thumbnail_url"].format(width="1920", height="1080")
                        link = f"https://www.twitch.tv/{streamer_name}"
                        top_streamers[i] = {"streamer": streamer_name,
                                              "viewer_count": viewer_count,
                                              "follower_count": follower_count,
                                              "title": stream_title,
                                              "started_at": started_at,
                                              "language": language,
                                              "thumbnail": thumbnail_url,
                                              "link": link}
                    return top_streamers
                else:
                    return(f"Error {response.status}: Could not retrieve top streamers for category {category_id}")


    async def get_api_points(self):
        """
        Get API points remaining
        
        Returns
        -------
        int
            API points remaining
        """
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.users) as response:
                api_points = int(response.headers.get("Ratelimit-Remaining"))
                return api_points


    async def get_category_image(self, category_id):
        """
        Get image for category ID
        
        Parameters
        ----------
        category_id : str
            Category ID
        
        Returns
        -------
        str
            Image URL for category ID
        """
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"id": category_id}
        url = f"https://api.twitch.tv/helix/games?id={category_id}"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data["data"][0]["box_art_url"].format(width="320", height="440")
                    return image_url
                else:
                    return f"Error {response.status}: Could not retrieve image for category {category_id}"

