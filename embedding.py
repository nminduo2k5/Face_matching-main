import os
import pandas as pd
import requests
from urllib.parse import urlparse

def download_public_google_sheet_to_csv(
    sheet_url="https://docs.google.com/spreadsheets/d/1dsvLOg_W4fn1g1hCNUUw_5WwfBnJn9_VVcvH0NjOOBY/edit#gid=0", 
    csv_file_path="data.csv",
    header=0,  # Assuming the first row is the header
    skiprows=None  # Adjust if you need to skip specific rows
):
    """
    Download a public Google Sheet as a CSV file.
    
    Parameters:
    - sheet_url: str, URL of the public Google Sheet.
    - csv_file_path: str, path where the CSV file will be saved.
    - header: int or list of int, row number(s) to use as the column names.
    - skiprows: list-like, int or callable, rows to skip at the beginning.
    """
    # Convert the Google Sheets URL to CSV export URL
    csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    
    try:
        # Read the CSV with error handling
        df = pd.read_csv(csv_url, header=header, skiprows=skiprows, on_bad_lines='skip', encoding='utf-8')
    except pd.errors.ParserError as e:
        print(f"ParserError encountered: {e}")
        # Attempt to read again, skipping bad lines
        df = pd.read_csv(csv_url, header=header, skiprows=skiprows, on_bad_lines='skip', encoding='utf-8')
        print("Skipped bad lines in the CSV.")
    
    df.to_csv(csv_file_path, index=False)
    print(f"Downloaded CSV file: {csv_file_path}")
    return df

def convert_google_drive_link(link):
    """
    Convert Google Drive links for direct download or folder recognition.

    Parameters:
    - link: str, Google Drive link.

    Returns:
    - Tuple(str, bool), direct download link (or original link) and a flag indicating if it's a folder.
    """
    if not isinstance(link, str):
        print(f"Invalid value: {link}")
        return "", False

    try:
        if "drive.google.com" in link:
            # Handle Google Drive file links
            if '/file/d/' in link:
                file_id = link.split('/file/d/')[1].split('/')[0]
                return f"https://drive.google.com/uc?export=download&id={file_id}", False
            # Handle Google Drive folder links
            elif '/folders/' in link or 'drive/folders/' in link:
                return link, True  # It's a folder
        return link, False
    except IndexError:
        print(f"Error processing link: {link}")
        return link, False

def download_images_from_csv(
    df, 
    employee_code_column='MÃ SINH VIÊN', 
    link_column='LINK ẢNH',
    faces_dir='./faces/'
):
    """
    Create directories based on employee codes and download images from the provided links.
    
    Parameters:
    - df: DataFrame, the downloaded CSV data.
    - employee_code_column: str, column name for employee codes.
    - link_column: str, column name for image links.
    - faces_dir: str, base directory to save downloaded images.
    """
    # Supported image MIME types
    valid_image_formats = [
        'image/jpeg', 'image/png', 'image/gif', 
        'image/bmp', 'image/heif', 'image/heic', 'image/webp'
    ]
    
    successful_downloads = 0  # Counter for successful downloads

    for index, row in df.iterrows():
        employee_code = row.get(employee_code_column, None)
        link = row.get(link_column, None)
        
        if pd.isna(employee_code) or pd.isna(link):
            print(f"Missing data in row {index + 1}. Skipping...")
            continue

        # Convert Google Drive link if necessary
        direct_link, is_folder = convert_google_drive_link(link)

        if is_folder:
            print(f"Employee {employee_code} has a folder link: {direct_link}")
            continue  # Skip folders
        else:
            if direct_link:  # Ensure the link is not empty
                try:
                    response = requests.get(direct_link, timeout=10)
                    content_type = response.headers.get('Content-Type', '').split(';')[0]  # Handle cases like 'image/jpeg; charset=UTF-8'

                    # Check if the content type is a valid image format
                    if response.status_code == 200 and content_type in valid_image_formats:
                        # Extract file extension from content type
                        file_extension = content_type.split('/')[1]  # e.g., 'image/jpeg' -> 'jpeg'
                        
                        folder_path = os.path.join(faces_dir, str(employee_code))
                        os.makedirs(folder_path, exist_ok=True)

                        image_path = os.path.join(folder_path, f"{employee_code}.{file_extension}")
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Downloaded image for employee {employee_code} as {image_path}")
                        successful_downloads += 1
                    else:
                        print(f"Invalid image format or failed to download from {link}. Status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Request error for {link}: {e}")
                except Exception as e:
                    print(f"Unexpected error for {link}: {e}")

    # Summary of downloads
    print(f"Total successful downloads: {successful_downloads}")

# Execute the functions
if __name__ == "__main__":
    try:
        df = download_public_google_sheet_to_csv()
        download_images_from_csv(df)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")