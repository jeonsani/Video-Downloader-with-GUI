import imgui
import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import yt_dlp
import os
from youtubesearchpython import VideosSearch

def progress_hook(d):
    global download_progress
    if d['status'] == 'downloading':
        # Calculate progress percentage
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        if total_bytes:
            percentage = (d['downloaded_bytes'] / total_bytes) * 100
            speed = d.get('speed', 0)
            if speed:
                speed_mb = speed / 1024 / 1024  # Convert to MB/s
                download_progress = f"Downloading: {percentage:.1f}% (Speed: {speed_mb:.1f} MB/s)"
            else:
                download_progress = f"Downloading: {percentage:.1f}%"
    elif d['status'] == 'finished':
        download_progress = "Download completed, processing file..."

def search_videos(keyword, limit=5):
    try:
        results = VideosSearch(keyword, limit=limit).result()['result']
        return [{'title': video['title'], 
                'url': video['link']} 
                for video in results]
    except Exception as e:
        return []

def download_content(url, path, content_type='video', format_option='MP4 (Video + Audio)', quality='Best', is_bulk=False, bulk_type='', bulk_limit=5):
    global download_progress
    try:
        os.makedirs(path, exist_ok=True)
        
        if is_bulk:
            if bulk_type == 'YouTube Search':
                keyword = url
                search_url = f"ytsearch{bulk_limit}:{keyword}"
                
                # Set format based on format_option
                if format_option == 'MP3 (Audio Only)':
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{path}/%(title)s.%(ext)s',
                        'progress_hooks': [progress_hook],
                        'max_downloads': bulk_limit,
                        'default_search': 'ytsearch',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': quality.replace('kbps', ''),
                        }]
                    }
                else:  # MP4
                    format_spec = {
                        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                        '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                        '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                        'Best': 'best'
                    }
                    ydl_opts = {
                        'format': format_spec[quality],
                        'outtmpl': f'{path}/%(title)s.%(ext)s',
                        'progress_hooks': [progress_hook],
                        'max_downloads': bulk_limit,
                        'default_search': 'ytsearch'
                    }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([search_url])
            elif bulk_type == 'Pinterest Board':
                # Pinterest bulk download options
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': f'{path}/%(title)s.%(ext)s',
                    'progress_hooks': [progress_hook],
                    'extract_flat': True,
                    'ignoreerrors': True,
                    'quiet': True,
                    'download_archive': 'downloaded.txt',
                }
            else:  # Other platforms
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': f'{path}/%(title)s.%(ext)s',
                    'progress_hooks': [progress_hook],
                    'ignoreerrors': True,
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return "Bulk download completed!"
        
        if content_type == 'images':
            if 'pinterest.com' in url:
                # Pinterest-specific options
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': f'{path}/%(title)s-%(id)s.%(ext)s',
                    'progress_hooks': [progress_hook],
                    'extract_flat': False,  # Changed from True
                    'writethumbnail': True,
                    'skip_download': False,
                    'ignoreerrors': True,
                    'quiet': False,  # Changed from True to see errors
                    # Add cookies if needed
                    'cookiesfrombrowser': ('chrome',),  # Use cookies from Chrome
                }
            else:
                # Regular image download options
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': f'{path}/%(title)s-%(id)s.%(ext)s',
                    'progress_hooks': [progress_hook],
                    'writethumbnail': True,
                    'ignoreerrors': True
                }
        else:  # video download
            format_spec = {
                'MP4 (Video + Audio)': {
                    '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                    'Best': 'best'
                },
                'MP3 (Audio Only)': {
                    'Best Quality': 'bestaudio/best',
                    '128kbps': 'bestaudio[abr<=128]/best',
                    '64kbps': 'bestaudio[abr<=64]/best'
                }
            }
            ydl_opts = {
                'format': format_spec[format_option][quality],
                'outtmpl': f'{path}/%(title)s.%(ext)s',
                'progress_hooks': [progress_hook],
            }
            
            if format_option == 'MP3 (Audio Only)':
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "Download completed!"
    except Exception as e:
        return f"An error occurred: {e}"

def get_video_info(url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'N/A'),
                'duration': f"{int(info.get('duration', 0) / 60)}:{int(info.get('duration', 0) % 60):02d}",
                'views': info.get('view_count', 'N/A'),
                'uploader': info.get('uploader', 'N/A')
            }
    except Exception as e:
        return None

def main():
    # Initialize GLFW
    if not glfw.init():
        return

    # Create a window without decorations
    glfw.window_hint(glfw.DECORATED, False)
    window_width, window_height = 400, 220
    window = glfw.create_window(window_width, window_height, "Video Downloader", None, None)
    if not window:
        glfw.terminate()
        return

    # Center the window on the screen
    monitor = glfw.get_primary_monitor()
    mode = glfw.get_video_mode(monitor)
    screen_width = mode.size.width
    screen_height = mode.size.height
    glfw.set_window_pos(
        window,
        (screen_width - window_width) // 2,
        (screen_height - window_height) // 2
    )

    glfw.make_context_current(window)

    # Initialize ImGui
    imgui.create_context()
    impl = GlfwRenderer(window)
    
    # Set ImGui style
    style = imgui.get_style()
    style.window_padding = (10, 10)
    style.window_rounding = 0
    style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.1, 0.1, 0.1, 1)
    style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (0.1, 0.1, 0.1, 1)
    style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.1, 0.1, 0.1, 1)
    style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.2, 0.2, 0.2, 1)

    url = ""
    path = ""
    message = ""
    video_info = None
    show_info = False
    content_types = ['Video/Audio', 'Images', 'Bulk Download']
    current_content = content_types[0]
    format_options = ['MP4 (Video + Audio)', 'MP3 (Audio Only)']
    current_format = format_options[0]
    quality_options = {
        'MP4 (Video + Audio)': ['1080p', '720p', '480p', 'Best'],
        'MP3 (Audio Only)': ['Best Quality', '128kbps', '64kbps']
    }
    current_quality = quality_options[current_format][0]
    bulk_types = ['YouTube Search', 'Pinterest Board', 'Instagram Profile', 'Twitter Media']
    current_bulk_type = bulk_types[0]
    bulk_limit = 5

    # Add vsync to reduce tearing
    glfw.swap_interval(1)

    # Modify window dragging variables
    is_dragging = False
    last_x = 0
    last_y = 0

    # Add global variable for progress
    global download_progress
    download_progress = ""

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        # Simplified window dragging
        mouse_x, mouse_y = glfw.get_cursor_pos(window)
        
        if imgui.is_mouse_clicked(0):
            if mouse_y < 30:  # Top bar area
                is_dragging = True
                last_x, last_y = mouse_x, mouse_y
        
        if not glfw.get_mouse_button(window, 0):
            is_dragging = False
            
        if is_dragging:
            dx = mouse_x - last_x
            dy = mouse_y - last_y
            x, y = glfw.get_window_pos(window)
            glfw.set_window_pos(window, int(x + dx), int(y + dy))
            last_x, last_y = mouse_x, mouse_y

        imgui.new_frame()

        # Set the window to be the same size as the GLFW window
        viewport_width, viewport_height = glfw.get_window_size(window)
        imgui.set_next_window_size(viewport_width, viewport_height)
        imgui.set_next_window_position(0, 0)
        
        imgui.begin("Video Downloader", 
                   flags=imgui.WINDOW_NO_TITLE_BAR | 
                         imgui.WINDOW_NO_RESIZE)

        # Add close and minimize buttons
        window_width, _ = glfw.get_window_size(window)
        
        # Close button
        imgui.set_cursor_pos((window_width - 50, 5))
        if imgui.button("X", 20, 20):
            glfw.set_window_should_close(window, True)
            
        # Minimize button
        imgui.set_cursor_pos((window_width - 80, 5))
        if imgui.button("-", 20, 20):
            glfw.iconify_window(window)

        # Reset cursor for main content
        imgui.set_cursor_pos((10, 35))
        
        if current_content == 'Bulk Download':
            # Bulk type selection
            if imgui.begin_combo("Bulk Type", current_bulk_type):
                for bulk_type in bulk_types:
                    is_selected = (current_bulk_type == bulk_type)
                    if imgui.selectable(bulk_type, is_selected)[0]:
                        current_bulk_type = bulk_type
                    if is_selected:
                        imgui.set_item_default_focus()
                imgui.end_combo()

            if current_bulk_type == 'YouTube Search':
                imgui.text("Enter search keyword:")
                changed, url = imgui.input_text("Keyword##url", url, 256)
                
                # Add format selection for bulk downloads
                if imgui.begin_combo("Format", current_format):
                    for format_opt in format_options:
                        is_selected = (current_format == format_opt)
                        if imgui.selectable(format_opt, is_selected)[0]:
                            current_format = format_opt
                            current_quality = quality_options[current_format][0]
                        if is_selected:
                            imgui.set_item_default_focus()
                    imgui.end_combo()

                if imgui.begin_combo("Quality", current_quality):
                    for quality in quality_options[current_format]:
                        is_selected = (current_quality == quality)
                        if imgui.selectable(quality, is_selected)[0]:
                            current_quality = quality
                        if is_selected:
                            imgui.set_item_default_focus()
                    imgui.end_combo()
            else:
                imgui.text(f"Enter {current_bulk_type} URL:")
                changed, url = imgui.input_text("URL##url", url, 256)
            
            changed, bulk_limit = imgui.slider_int("Number of items", bulk_limit, 1, 20)
        else:
            changed, url = imgui.input_text("URL##url", url, 256)

        changed, path = imgui.input_text("Save Path", path, 256)

        # Info button
        if imgui.button("Get Info"):
            video_info = get_video_info(url)
            show_info = True

        # Show video info if available
        if show_info and video_info:
            imgui.text("Video Information:")
            imgui.text(f"Title: {video_info['title']}")
            imgui.text(f"Duration: {video_info['duration']}")
            imgui.text(f"Views: {video_info['views']}")
            imgui.text(f"Uploader: {video_info['uploader']}")
        elif show_info:
            imgui.text("Could not fetch video information")

        # Content type selection
        if imgui.begin_combo("Content Type", current_content):
            for content_type in content_types:
                is_selected = (current_content == content_type)
                if imgui.selectable(content_type, is_selected)[0]:
                    current_content = content_type
                if is_selected:
                    imgui.set_item_default_focus()
            imgui.end_combo()

        # Only show format/quality options for video/audio
        if current_content == 'Video/Audio':
            if imgui.begin_combo("Format", current_format):
                for format_opt in format_options:
                    is_selected = (current_format == format_opt)
                    if imgui.selectable(format_opt, is_selected)[0]:
                        current_format = format_opt
                        current_quality = quality_options[current_format][0]
                    if is_selected:
                        imgui.set_item_default_focus()
                imgui.end_combo()

            if imgui.begin_combo("Quality", current_quality):
                for quality in quality_options[current_format]:
                    is_selected = (current_quality == quality)
                    if imgui.selectable(quality, is_selected)[0]:
                        current_quality = quality
                    if is_selected:
                        imgui.set_item_default_focus()
                imgui.end_combo()

        if imgui.button("Download"):
            content_type = 'images' if current_content == 'Images' else 'video'
            is_bulk = current_content == 'Bulk Download'
            message = download_content(url, path, content_type, current_format, current_quality, is_bulk, current_bulk_type, bulk_limit)

        imgui.text(message)
        if download_progress:
            imgui.text(download_progress)  # Show download progress

        imgui.end()

        # Rendering
        gl.glClearColor(0.1, 0.1, 0.1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()

if __name__ == '__main__':
    download_progress = ""  # Initialize global variable
    main()
