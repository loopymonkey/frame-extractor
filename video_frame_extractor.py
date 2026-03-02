from pathlib import Path
import traceback

import cv2
import flet as ft

VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v"]


class VideoFrameExtractor:
    def __init__(self) -> None:
        self.selected_files: list[str] = []
        self.output_directory: str | None = None

    def output_path_for(self, video_path: str, use_default_output: bool) -> str:
        video_file = Path(video_path)
        if use_default_output or not self.output_directory:
            output_dir = video_file.parent / "RESIZED"
        else:
            output_dir = Path(self.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        candidate = output_dir / f"{video_file.stem}_first_frame.jpg"
        counter = 1
        while candidate.exists():
            candidate = output_dir / f"{video_file.stem}_first_frame_{counter}.jpg"
            counter += 1
        return str(candidate)

    def resize_frame(
        self, frame, max_width: int | None, max_height: int | None
    ):
        if max_width is None and max_height is None:
            return frame

        height, width = frame.shape[:2]
        scale_w = (max_width / width) if max_width else None
        scale_h = (max_height / height) if max_height else None

        if scale_w and scale_h:
            scale = min(scale_w, scale_h, 1.0)
        else:
            scale = min(scale_w or scale_h or 1.0, 1.0)

        if scale >= 1.0:
            return frame

        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))
        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def extract_first_frame(
        self,
        video_path: str,
        max_width: int | None,
        max_height: int | None,
        use_default_output: bool,
    ) -> tuple[bool, str]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, f"Could not open {Path(video_path).name}"

        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                return False, f"Could not read first frame from {Path(video_path).name}"

            frame = self.resize_frame(frame, max_width, max_height)
            output_path = self.output_path_for(video_path, use_default_output)
            ok = cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not ok:
                return False, f"Failed to write JPG for {Path(video_path).name}"

            return True, f"Saved {Path(output_path).name}"
        except Exception as ex:
            return False, f"Error for {Path(video_path).name}: {ex}"
        finally:
            cap.release()


def _main(page: ft.Page) -> None:
    page.title = "Video Frame Extractor"
    page.window.width = 760
    page.window.height = 620
    page.padding = 20

    extractor = VideoFrameExtractor()

    file_list = ft.ListView(expand=True, spacing=8, padding=8, auto_scroll=False)
    status_text = ft.Text("Select one or more videos to extract the first frame.", size=14, color="grey")
    output_folder_text = ft.Text("Output folder: RESIZED folder next to each video", size=12, color="grey")
    progress_bar = ft.ProgressBar(width=420, visible=False, value=0)
    max_width_input = ft.TextField(label="Max width (px)", width=170, hint_text="Optional")
    max_height_input = ft.TextField(label="Max height (px)", width=170, hint_text="Optional")
    use_default_output_checkbox = ft.Checkbox(
        label="Use default output folder (RESIZED next to each video)",
        value=True,
    )
    drop_paths_input = ft.TextField(
        label="Drag video files here or paste file paths (one per line)",
        hint_text="/Users/you/Desktop/clip.mp4",
        multiline=True,
        min_lines=3,
        max_lines=4,
    )

    def clean_dragged_path(raw_path: str) -> str:
        path = raw_path.strip().strip('"').strip("'")
        if path.startswith("file://"):
            path = path[7:]
        return path.replace("%20", " ")

    def add_files(paths: list[str]) -> tuple[int, int]:
        added = 0
        skipped = 0
        for raw_path in paths:
            file_path = clean_dragged_path(raw_path)
            if not file_path:
                continue
            path_obj = Path(file_path).expanduser()
            if not path_obj.exists() or not path_obj.is_file():
                skipped += 1
                continue
            if path_obj.suffix.lower().lstrip(".") not in VIDEO_EXTENSIONS:
                skipped += 1
                continue
            resolved = str(path_obj.resolve())
            if resolved in extractor.selected_files:
                skipped += 1
                continue
            extractor.selected_files.append(resolved)
            added += 1
        return added, skipped

    def render_selected_files() -> None:
        file_list.controls.clear()
        for file_path in extractor.selected_files:
            file_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.VIDEOCAM, color="blue"),
                            ft.Text(Path(file_path).name, size=13, weight=ft.FontWeight.W_400),
                        ]
                    ),
                    padding=10,
                    border=ft.Border.all(1, "grey"),
                    border_radius=5,
                )
            )

    file_picker = ft.FilePicker()
    output_folder_picker = ft.FilePicker()
    page.services.append(file_picker)
    page.services.append(output_folder_picker)

    choose_output_folder_button = ft.Button(
        "Choose Output Folder",
        icon=ft.Icons.FOLDER_OPEN,
        disabled=True,
    )

    def refresh_output_folder_text() -> None:
        if use_default_output_checkbox.value:
            output_folder_text.value = "Output folder: RESIZED folder next to each video"
            output_folder_text.color = "grey"
            choose_output_folder_button.disabled = True
        elif extractor.output_directory:
            output_folder_text.value = f"Output folder: {extractor.output_directory}"
            output_folder_text.color = "green"
            choose_output_folder_button.disabled = False
        else:
            output_folder_text.value = "Output folder: choose a custom folder"
            output_folder_text.color = "orange"
            choose_output_folder_button.disabled = False

    async def pick_files(_: ft.ControlEvent) -> None:
        files = await file_picker.pick_files(
            dialog_title="Select Video Files",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if not files:
            return
        extractor.selected_files = []
        add_files([f.path for f in files if f.path])
        render_selected_files()
        status_text.value = f"{len(extractor.selected_files)} file(s) selected"
        status_text.color = "green"
        refresh_output_folder_text()
        page.update()

    async def choose_output_folder(_: ft.ControlEvent) -> None:
        selected_path = await output_folder_picker.get_directory_path(
            dialog_title="Choose Output Folder"
        )
        if not selected_path:
            return
        extractor.output_directory = selected_path
        refresh_output_folder_text()
        page.update()

    def on_output_mode_changed(_: ft.ControlEvent) -> None:
        refresh_output_folder_text()
        page.update()

    choose_output_folder_button.on_click = choose_output_folder
    use_default_output_checkbox.on_change = on_output_mode_changed

    def parse_limit(value: str, label: str) -> tuple[bool, int | None]:
        raw = (value or "").strip()
        if not raw:
            return True, None
        try:
            parsed = int(raw)
        except ValueError:
            status_text.value = f"{label} must be a whole number."
            status_text.color = "red"
            return False, None
        if parsed <= 0:
            status_text.value = f"{label} must be greater than 0."
            status_text.color = "red"
            return False, None
        return True, parsed

    def process_videos(_: ft.ControlEvent) -> None:
        if not extractor.selected_files:
            status_text.value = "Select video files first."
            status_text.color = "red"
            page.update()
            return

        width_ok, max_width = parse_limit(max_width_input.value, "Max width")
        height_ok, max_height = parse_limit(max_height_input.value, "Max height")
        if not width_ok or not height_ok:
            page.update()
            return

        if not use_default_output_checkbox.value and not extractor.output_directory:
            status_text.value = "Choose a custom output folder or enable the default output folder."
            status_text.color = "red"
            page.update()
            return

        total = len(extractor.selected_files)
        progress_bar.visible = True
        progress_bar.value = 0
        status_text.value = "Processing videos..."
        status_text.color = "blue"
        page.update()

        results: list[tuple[bool, str]] = []
        for idx, video_path in enumerate(extractor.selected_files, start=1):
            success, message = extractor.extract_first_frame(
                video_path=video_path,
                max_width=max_width,
                max_height=max_height,
                use_default_output=bool(use_default_output_checkbox.value),
            )
            results.append((success, message))
            progress_bar.value = idx / total
            page.update()

        progress_bar.visible = False
        success_count = sum(1 for success, _ in results if success)
        status_text.value = f"Complete: {success_count}/{total} extracted."
        status_text.color = "green" if success_count == total else "orange"

        file_list.controls.clear()
        for (success, message), file_path in zip(results, extractor.selected_files):
            icon = ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR
            icon_color = "green" if success else "red"
            file_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(icon, color=icon_color, size=20),
                                    ft.Text(Path(file_path).name, size=13, weight=ft.FontWeight.W_500),
                                ]
                            ),
                            ft.Text(message, size=11, color="grey", italic=True),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    border=ft.Border.all(1, "grey"),
                    border_radius=5,
                )
            )
        page.update()

    def add_dropped_paths(_: ft.ControlEvent) -> None:
        raw = drop_paths_input.value or ""
        lines = [line for line in raw.splitlines() if line.strip()]
        if not lines:
            status_text.value = "No paths found to add."
            status_text.color = "red"
            page.update()
            return

        added, skipped = add_files(lines)
        render_selected_files()
        if added:
            status_text.value = f"Added {added} file(s), skipped {skipped}."
            status_text.color = "green" if skipped == 0 else "orange"
            drop_paths_input.value = ""
        else:
            status_text.value = f"No valid video files added. Skipped {skipped}."
            status_text.color = "red"
        page.update()

    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Video Frame Extractor", size=26, weight=ft.FontWeight.BOLD, color="blue"),
                            ft.Text("Extract the first frame from selected videos as JPG images.", size=14, color="grey"),
                        ],
                        spacing=5,
                    ),
                    padding=ft.padding.only(bottom=20),
                ),
                ft.Row(
                    [
                        ft.Button("Select Video Files", icon=ft.Icons.FOLDER, on_click=pick_files),
                        choose_output_folder_button,
                        ft.Button(
                            "Extract Frames",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=process_videos,
                            style=ft.ButtonStyle(bgcolor="blue", color="white"),
                        ),
                    ],
                    spacing=10,
                ),
                ft.Container(height=10),
                status_text,
                ft.Row([max_width_input, max_height_input], spacing=10),
                use_default_output_checkbox,
                output_folder_text,
                progress_bar,
                ft.Container(height=10),
                drop_paths_input,
                ft.Row([ft.Button("Add Dropped/Pasted Paths", icon=ft.Icons.ADD, on_click=add_dropped_paths)]),
                ft.Container(height=10),
                ft.Container(content=file_list, border=ft.Border.all(1, "grey"), border_radius=5, padding=5, expand=True),
            ],
            expand=True,
        )
    )


def main(page: ft.Page) -> None:
    try:
        _main(page)
    except Exception:
        error_text = traceback.format_exc()
        print(error_text, flush=True)
        page.clean()
        page.scroll = ft.ScrollMode.AUTO
        page.add(
            ft.Text("Startup error", color="red", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("The app failed while building the UI. Traceback:", size=13),
            ft.Text(error_text, selectable=True, size=11),
        )
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
