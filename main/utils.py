import requests

def reverse_geocode(lat, lon):
    try:
        response = requests.get(
            f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1',
            headers={'User-Agent': 'YourAppName/1.0'}  # Replace with your application name
        )
        response.raise_for_status()
        data = response.json()
        print("Reverse Geocode Response:", data)  # Print the full response
        address = data.get('address', {})
        # Adjust this based on actual response structure
        location_name = address.get('road') or address.get('suburb') or address.get('city') or address.get('town') or 'Unknown location'
        return location_name
    except Exception as e:
        print(f'Error in reverse_geocode: {e}')
        return 'Unknown location'
