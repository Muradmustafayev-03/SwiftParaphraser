from api import *


def preprocess(unique_id: str, project: dict) -> dict:
    """
    Preprocess the project. Remove comments and empty lines, change 'class func' to 'static func'.

    :param unique_id: str, unique id of the project
    :param project: dict, project to preprocess
    :return: dict, preprocessed project
    """

    assert receive_notification(unique_id) is not None, 'Connection interrupted.'
    notify(unique_id, 'Preprocessing...')

    assert receive_notification(unique_id) is not None, 'Connection interrupted.'
    notify(unique_id, 'Removing comments...')
    project = apply_to_project(project, remove_comments)

    assert receive_notification(unique_id) is not None, 'Connection interrupted.'
    notify(unique_id, 'Removing empty lines...')
    project = apply_to_project(project, remove_empty_lines)

    notify(unique_id, 'Finished preprocessing the project...')
    return project


def pipeline(unique_id: str, project: dict,
             condition_transformation=True, loop_transformation=True,
             type_renaming=True, types_to_rename=('struct', 'enum', 'protocol'),
             file_renaming=False, function_transformation=True, variable_renaming=True, comment_adding=True):
    """
    Project paraphrasing pipeline.

    :param unique_id: str, unique id of the project
    :param project: dict, project to paraphrase
    :param condition_transformation: bool, whether to transform conditions, stable, recommended being True
    :param loop_transformation: bool, whether to transform loops, stable, recommended being True
    :param type_renaming: bool, whether to rename types, semi-stable, recommended being True for smaller projects
    :param types_to_rename: tuple of strings, types to rename, recommended being ('struct', 'enum', 'protocol')
    :param file_renaming: bool, whether to rename files, causes `Name` not found in Storyboard error, recommended being False
    :param function_transformation: bool, whether to restructure functions, unstable, recommended being True
    :param variable_renaming: bool, whether to rename variables, stable, recommended being True
    :param comment_adding: bool, whether to add comments, stable, recommended being True (takes a long time)
    """
    notify(unique_id, 'Started paraphrasing the project...')

    if condition_transformation:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Transforming conditions...')
        project = apply_to_project(project, transform_conditions, comment_adding=comment_adding)
        notify(unique_id, 'Finished transforming conditions.')

    if loop_transformation:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Transforming loops...')
        project = apply_to_project(project, transform_loops, comment_adding=comment_adding)
        notify(unique_id, 'Finished transforming loops.')

    if type_renaming:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Renaming types...')
        type_names = parse_types_in_project(project, include_types=types_to_rename)
        if type_names:
            rename_map = generate_rename_map(type_names)
            project = rename_types(project, rename_map, rename_files=file_renaming)
        notify(unique_id, 'Finished renaming types.')

    if file_renaming:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Renaming files...')
        project = rename_files(project)
        notify(unique_id, 'Finished renaming files.')

    if function_transformation:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Restructuring functions...')
        project = apply_to_project(project, restructure_functions)

    if variable_renaming:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Renaming variables...')
        project = apply_to_project(project, rename_variables)
        notify(unique_id, 'Finished renaming variables.')

    if True:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Changing structs to classes...')
        project = apply_to_project(project, struct_to_class)
        notify(unique_id, 'Finished changing structs to classes.')

    if comment_adding:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Adding comments...')
        project = apply_to_project(project, add_comments)
        notify(unique_id, 'Finished adding comments.')

    notify(unique_id, 'Finished paraphrasing the project.')

    return project
