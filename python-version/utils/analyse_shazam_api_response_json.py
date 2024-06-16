import json

def analyse_shazam_api_response_json():
    # Load the JSON data from the file
    with open('/repos/SongRecTikTok/python-version/utils/shazam_api_response.json', 'r') as file:
        data = json.load(file)
    
    # Initialize a list to store the results
    results = []

    # Iterate through each item in the JSON data
    for item in data:
        file_path = item.get("file", "")
        sound_id = file_path.split('/')[-1].split('.')[0]

        result = item.get("result", {})
        track_info = result.get("track", {})
        share_info = track_info.get("share", {})
        images_info = track_info.get("images", {})
        
        # Extract the values as specified
        shazam_isrc = track_info.get("isrc", "N/A")
        shazam_image_url = images_info.get("background", "N/A")
        shazam_song_name = share_info.get("subject", "N/A")
        shazam_url = share_info.get("href", "N/A")
        
        # Append the extracted values to the results list
        results.append({
            "sound_id": sound_id,
            "shazam_isrc": shazam_isrc,
            "shazam_image_url": shazam_image_url,
            "shazam_song_name": shazam_song_name,
            "shazam_url": shazam_url
        })
    
    # Print the results
    for result in results:
        print(f"sound_id: {result['sound_id']}")
        print(f"shazam_isrc: {result['shazam_isrc']}")
        print(f"shazam_image_url: {result['shazam_image_url']}")
        print(f"shazam_song_name: {result['shazam_song_name']}")
        print(f"shazam_url: {result['shazam_url']}")
        print("\n")

if __name__ == "__main__":
    analyse_shazam_api_response_json()
