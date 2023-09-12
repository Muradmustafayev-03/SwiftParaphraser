from api import *


async def preprocess(project: dict) -> dict:
    """
    Preprocess the project. Remove comments and empty lines, change 'class func' to 'static func'.
    :param project: dict, project to preprocess
    :return: dict, preprocessed project
    """
    project = await apply_to_project(project, remove_comments)
    project = await apply_to_project(project, remove_empty_lines)
    return project


async def pipeline(project: dict,
                   condition_transformation=True, loop_transformation=True,
                   type_renaming=True, types_to_rename=('struct', 'enum', 'protocol'),
                   file_renaming=False, variable_renaming=True, comment_adding=True):
    """
    Project paraphrasing pipeline.

    :param project: dict, project to paraphrase
    :param condition_transformation: bool, whether to transform conditions, stable, recommended being True
    :param loop_transformation: bool, whether to transform loops, stable, recommended being True
    :param type_renaming: bool, whether to rename types, semi-stable, recommended being True for smaller projects
    :param types_to_rename: tuple of strings, types to rename, recommended being ('struct', 'enum', 'protocol')
    :param file_renaming: bool, whether to rename files, causes `Name` not found in Storyboard error, recommended being False
    :param variable_renaming: bool, whether to rename variables, stable, recommended being True
    :param comment_adding: bool, whether to add comments, stable, recommended being True (takes a long time)
    """

    if condition_transformation:
        project = await apply_to_project(project, transform_conditions)
        print('finished transforming conditions')

    if loop_transformation:
        project = await apply_to_project(project, transform_loops)
        print('finished transforming loops')

    if type_renaming:
        type_names = parse_types_in_project(project, include_types=types_to_rename)
        if type_names:
            rename_map = generate_rename_map(type_names)
            project = rename_types(project, rename_map, rename_files=file_renaming)
        print('finished renaming types')

    if variable_renaming:
        project = await apply_to_project(project, rename_variables)
        print('finished renaming local variables')

    if comment_adding:
        project = await apply_to_project(project, add_comments)
        print('finished adding comments')

    return project
