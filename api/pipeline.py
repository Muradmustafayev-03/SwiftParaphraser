from api import *


def preprocess(unique_id: str, path: str):
    """
    Preprocess the project. Remove comments and empty lines, change 'class func' to 'static func'.

    :param unique_id: str, unique id of the project
    :param path: path to the project to paraphrase
    :return: dict, preprocessed project
    """

    assert_notify(unique_id, 'Preprocessing...')

    assert_notify(unique_id, 'Removing comments...')
    apply_to_files(path, remove_comments)

    assert_notify(unique_id, 'Removing empty lines...')
    apply_to_files(path, remove_empty_lines)


def pipeline(unique_id: str, path: str,
             condition_transformation=True, loop_transformation=True,
             type_renaming=True, types_to_rename=('struct', 'enum', 'protocol'),
             file_renaming=False, function_transformation=True, variable_renaming=True, comment_adding=True):
    """
    Project paraphrasing pipeline.

    :param unique_id: str, unique id of the project
    :param path: path to the project to paraphrase
    :param condition_transformation: bool, whether to transform conditions, stable, recommended being True
    :param loop_transformation: bool, whether to transform loops, stable, recommended being True
    :param type_renaming: bool, whether to rename types, semi-stable, recommended being True for smaller projects
    :param types_to_rename: tuple of strings, types to rename, recommended being ('struct', 'enum', 'protocol')
    :param file_renaming: bool, whether to rename files, causes `Name` not found in Storyboard error, recommended being False
    :param function_transformation: bool, whether to restructure functions, unstable, recommended being True
    :param variable_renaming: bool, whether to rename variables, stable, recommended being True
    :param comment_adding: bool, whether to add comments, stable, recommended being True (takes a long time)
    """
    preprocess(unique_id, path)
    notify(unique_id, 'Finished preprocessing the project...')

    if condition_transformation:
        assert_notify(unique_id, 'Transforming conditions...')
        apply_to_files(path, transform_conditions, comment_adding=comment_adding)
        notify(unique_id, 'Finished transforming conditions.')

    if loop_transformation:
        assert_notify(unique_id, 'Transforming loops...')
        apply_to_files(path, transform_loops, comment_adding=comment_adding)
        notify(unique_id, 'Finished transforming loops.')

    if function_transformation:
        assert_notify(unique_id, 'Restructuring functions...')
        apply_to_files(path, restructure_functions)
        notify(unique_id, 'Finished restructuring functions.')

    if variable_renaming:
        assert_notify(unique_id, 'Renaming variables...')
        apply_to_files(path, rename_variables)
        notify(unique_id, 'Finished renaming variables.')

    if comment_adding:
        assert_notify(unique_id, 'Adding comments...')
        apply_to_files(path, add_comments)
        notify(unique_id, 'Finished adding comments.')

    project = dir_to_dict(path)

    type_names = parse_types_in_project(project, include_types=types_to_rename)
    types_in_frameworks = parse_types_in_frameworks(path)
    type_names = list(set(type_names) - set(types_in_frameworks))
    file_names = list_file_names(project)

    if type_renaming and type_names:
        assert_notify(unique_id, 'Renaming types...')
        project = rename_types(project, generate_rename_map(type_names))
        notify(unique_id, 'Finished renaming types.')

    if file_renaming and file_names:
        assert_notify(unique_id, 'Renaming files...')
        project = rename_files(project, generate_rename_map(file_names))
        notify(unique_id, 'Finished renaming files.')

    if True:
        assert_notify(unique_id, 'Adding dummy files...')
        project = add_dummy_files(project, path)
        notify(unique_id, 'Finished adding dummy files.')

    notify(unique_id, 'Finished paraphrasing the project.')

    assert_notify(unique_id, 'Saving paraphrased project...')
    dict_to_dir(project)
