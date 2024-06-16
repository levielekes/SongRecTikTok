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
        filename = file_path.split('/')[-1].split('.')[0]

        result = item.get("result", {})
        track_info = result.get("track", {})
        share_info = track_info.get("share", {})
        images_info = track_info.get("images", {})
        sections_info = track_info.get("sections", [])
        
        # Extract the values as specified
        isrc = track_info.get("isrc", "N/A")
        background_image = images_info.get("background", "N/A")
        subject = share_info.get("subject", "N/A")
        text = share_info.get("text", "N/A")
        
        # Append the extracted values to the results list
        results.append({
            "filename": filename,
            "isrc": isrc,
            "background_image": background_image,
            "subject": subject,
            "text": text
        })
    
    # Print the results
    for result in results:
        print(f"Filename: {result['filename']}")
        print(f"ISRC: {result['isrc']}")
        print(f"Background Image: {result['background_image']}")
        print(f"Subject: {result['subject']}")
        print(f"Text: {result['text']}")
        print("\n")

if __name__ == "__main__":
    analyse_shazam_api_response_json()
