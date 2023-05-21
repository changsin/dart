import os

import pandas as pd
import streamlit as st

from src.common.constants import (
    ErrorType,
    Type1Shape1Q,
    Type2SingleDoubleW,
    Type3PositionE,
    Type4UnusualCaseR,
    Type5ColorS,
    Type6BicycleD,
    BoundaryType2R,
    TypeRoadMarkerQ
)
from src.models.data_labels import DataLabels
from src.models.tasks_info import Task
from src.viewer import st_img_label
from src.viewer.image_manager import ImageManager
from src.common.logger import get_logger


logger = get_logger(__name__)

DEFAULT_SHAPE_COLOR = "magenta"


def _display_type_attributes(selected_shape: dict, key="1"):
    shape_type = selected_shape["shapeType"]
    attributes_dict = selected_shape["attributes"]
    if shape_type == "box":
        if attributes_dict:
            st.dataframe(pd.DataFrame.from_dict(attributes_dict, orient='index'))
    elif shape_type == "spline":
        type1value = attributes_dict.get('type1', None)
        type2value = attributes_dict.get('type2', None)
        type3value = attributes_dict.get('type3', None)
        type4value = attributes_dict.get('type4', None)
        type5value = attributes_dict.get('type5', None)
        type6value = attributes_dict.get('type6', None)

        st.selectbox("1.Shape1(Q)", Type1Shape1Q.get_all_types(),
                     key=f"1.Shape1(Q){key}",
                     index=Type1Shape1Q.get_index(type1value) if type1value else 0)
        st.selectbox("2.Single/Double(W)", Type2SingleDoubleW.get_all_types(),
                     key=f"2.Single/Double(W){key}",
                     index=Type2SingleDoubleW.get_index(type2value) if type2value else 0)
        st.selectbox("3.Position(E)", Type3PositionE.get_all_types(),
                     key=f"3.Position(E){key}",
                     index=Type3PositionE.get_index(type3value) if type3value else 0)
        st.selectbox("4.Unusual Case(R)", Type4UnusualCaseR.get_all_types(),
                     key=f"4.Unusual Case(R){key}",
                     index=Type4UnusualCaseR.get_index(type4value) if type4value else 0)
        st.selectbox("5.Color(S)", Type5ColorS.get_all_types(),
                     key=f"5.Color(S){key}",
                     index=Type5ColorS.get_index(type5value) if type5value else 0)
        st.selectbox("6.Bicycle(S)", Type6BicycleD.get_all_types(),
                     key=f"6.Bicycle(S){key}",
                     index=Type6BicycleD.get_index(type6value) if type6value else 0)
    elif shape_type == "boundary":
        type3value = attributes_dict.get('type3', None)
        boundary4value = attributes_dict.get('boundary', None)

        st.selectbox("3.Position(E)", Type3PositionE.get_all_types(),
                     key=f"3.Position(E){key}",
                     index=Type3PositionE.get_index(type3value) if type3value else 0)
        st.selectbox("2.Boundary type(R)", BoundaryType2R.get_all_types(),
                     key=f"2.Boundary type(R){key}",
                     index=BoundaryType2R.get_index(boundary4value) if boundary4value else 0)

    elif shape_type == "polygon":
        type_value = attributes_dict.get('type', None)
        st.selectbox("1.Road marker type(Q)", TypeRoadMarkerQ.get_all_types(),
                     key=f"1.Road marker type(Q){key}",
                     index=TypeRoadMarkerQ.get_index(type_value) if type_value else 0)


def main(selected_task: Task, is_second_viewer=False, error_codes=ErrorType.get_all_types()):
    def save(image_index: int, im: ImageManager):
        data_labels.images[image_index] = im.to_data_labels_image()
        data_labels.save(selected_task.anno_file_name)

    def refresh():
        save(st.session_state["image_index"], im)

    def previous_image():
        save(st.session_state["image_index"], im)
        if st.session_state["image_index"] > 0:
            st.session_state["image_index"] -= 1
        else:
            st.warning('This is the first image.')

    def next_image():
        save(st.session_state["image_index"], im)
        if st.session_state["image_index"] < len(st.session_state["img_files"]) - 1:
            st.session_state["image_index"] += 1
        else:
            st.warning('This is the last image.')

    def go_to_image():
        save(st.session_state["image_index"], im)
        selected_option = st.session_state["img_file"]
        image_index = st.session_state["img_files"].index(selected_option.split(") ")[-1])
        st.session_state["image_index"] = image_index

    def viewer_menu():
        # Sidebar: show status
        n_files = len(st.session_state["img_files"])
        # Main content: review images
        image_index = st.session_state['image_index']

        if image_index >= n_files:
            st.session_state['image_index'] = 0
            image_index = 0

        # Modify the select_box to include the file index prefix
        select_box_options = [f"({i + 1}/{n_files}) {filename}" for i, filename in enumerate(st.session_state["img_files"])]
        st.selectbox(" ",
                     select_box_options,
                     index=st.session_state["image_index"],
                     on_change=go_to_image,
                     key="img_file")

        col1, col2, col3 = st.columns(3)
        col1.button(label="< Previous", on_click=previous_image)
        col2.button(label="Refresh", on_click=refresh)
        col3.button(label="Next >", on_click=next_image)

        return image_index

    def call_frontend(im: ImageManager, image_index: int) -> dict:
        resized_img = im.resizing_img()
        resized_shapes = im.get_downscaled_shapes()
        shape_color = _pick_color(resized_shapes[0].get('label'), DEFAULT_SHAPE_COLOR)

        return st_img_label(resized_img, shape_color=shape_color, shape_props=resized_shapes,
                            key=f"{image_index}_2" if is_second_viewer else f"{image_index}_1")

    def process_selected_shape(selected_shape: dict):
        scaled_shape = im.upscale_shape(selected_shape)
        selected_shape_id = selected_shape["shape_id"]
        # if shape_id is new, it's an untagged label
        if not im.get_shape_by_id(selected_shape_id):
            im.add_shape(scaled_shape)
            st.write("Untagged box added")

        return scaled_shape

    def _pick_color(label: str, default_color: str) -> str:
        color_dict = {
            'boundary': 'blue',
            'spline': 'green',
            'polygon': 'purple'
        }
        return color_dict.get(label, default_color)

    # Load up the images and the labels
    data_labels = DataLabels.load(selected_task.anno_file_name)
    if not data_labels:
        st.warning("Data labels are empty")
        return

    # set session states
    image_filenames = [os.path.join("data", image.name) for image in data_labels.images]
    if not st.session_state.get('image_index'):
        st.session_state["img_files"] = image_filenames
        st.session_state["image_index"] = 0
    else:
        st.session_state["img_files"] = image_filenames

    image_index = st.session_state["image_index"]
    if not is_second_viewer:
        image_index = viewer_menu()
    task_folder = os.path.dirname(selected_task.anno_file_name)
    image_filename = os.path.join(task_folder, image_filenames[image_index])
    im = ImageManager(image_filename, data_labels.images[image_index])

    # call the frontend
    selected_shape = call_frontend(im, image_index)
    if selected_shape:
        scaled_shape = process_selected_shape(selected_shape)
        # present 3 columns for the selected shape
        selected_shape_id = selected_shape['shape_id']
        key = f"{selected_shape_id}_{is_second_viewer}"
        col1, col2, col3 = st.columns(3)

        # thumbnail image
        with col1:
            preview_img = im.get_preview_thumbnail(scaled_shape)
            if preview_img:
                preview_img.thumbnail((200, 200))
                col1.image(preview_img)
                st.write(scaled_shape["label"])
            points = selected_shape["points"]
            st.dataframe(pd.DataFrame(points))

        # attributes
        with col2:
            _display_type_attributes(selected_shape, key=key)

        # verification result
        with col3:
            default_index = 0
            verification_result = im.get_shape_by_id(selected_shape_id)['verification_result']
            if verification_result:
                error_code = verification_result['error_code']
                default_index = error_codes.index(error_code)

            comment = ""
            select_label = col3.selectbox("Error",
                                          error_codes,
                                          key=f"error_{selected_shape_id}_{key}",
                                          index=default_index)
            if select_label:
                if not verification_result:
                    verification_result = dict()
                default_comment = verification_result.get('comment', "")
                comment = col3.text_input("Comment", default_comment, key={key})

            # save the verification result
            im.set_review(selected_shape_id, select_label, comment)

            if verification_result and verification_result['error_code'] == 'Untagged':
                delete_shape = st.button("Delete", key=key)
                if delete_shape:
                    im.remove_shape(selected_shape)
                    logger.info(f"Deleted {selected_shape}")

            save(image_index, im)


#
# if __name__ == "__main__":
#     main()
