"""
#
# # Renamer Maya objects with suffix numeric or alphabetic
#
"""
try:
    import maya.cmds as cmds
    import pymel.core as pm
    import re
    import string
    from itertools import combinations_with_replacement as cwr
except Exception as e:
    cmds.error(e)


class RENAMER(object):
    """
    # # Class for rename object list
    """
    def __init__(self, oldNames=None, modelName=None, numFrequency = 3):
        """
        #
        ## __init__ method of the renamer class
        #
        :param oldNames: list of objects

        :param modelName: pattern of name prefix_<num>_suffix,
                                       or prefix_<str>_suffix,
                                       or prefix_<str>_middle_<num>suffix.
                          The amount of <str> and/or <num> will result with amount of decimal places of number or string
                          Example: prefix_<num>_suffix = prefix_1_suffix; prefix_<num><num>_suffix = preffix_01_suffix

        :param numFrequency: if the modelName has <str> and <num>, this number dictate how often the <str> is passed to next
                            Example: len(selection) = 5; numFrequency = 2, modelName='prefix_<str>_middle_<num>_suffix'
                                     Result: prefix_A_middle_1_suffix, prefix_A_middle_2_suffix
                                             prefix_B_middle_1_suffix, prefix_B_middle_2_suffix
                                             prefix_C_middle_1_suffix

        """

        self.objectsList = []
        if not oldNames:
            # get list of selected objects
            self.objectsList = get_selection()
        else:
            # convert objects for pynode
            for i in oldNames:
                node = pm.PyNode(i)
                self.objectsList.append(node.fullPath())

        self.modelName = modelName

        self.strPattern = '<str>'
        self.numPattern = '<num>'
        self.lPriority = numFrequency

        self.renameObjects()

    def renameObjects(self):
        """
        Rename selected objects
        :return: None
        """

        # if only string pattern
        if re.search(self.strPattern, self.modelName) and not re.search(self.numPattern, self.modelName):
            # occurrences of string pattern
            strOcc = len(re.findall(self.strPattern, self.modelName))
            splitList = self.modelName.split(self.strPattern)
            prefix = splitList[0]
            suffix = splitList[-1]

            # rename object List
            if self.objectsList:
                newNames = alphabetical_constructor(prefix          =   prefix,
                                                    suffix          =   suffix,
                                                    decimalPlaces   =   strOcc,
                                                    lenSel          =   len(self.objectsList))
                for i in range(len(self.objectsList)):
                    name=newNames.next()
                    pm.rename(self.objectsList[i], name)

        # if only number pattern
        elif re.search(self.numPattern, self.modelName) and not re.search(self.strPattern, self.modelName):
            # occurrences of numeric pattern
            numOcc = len(re.findall(self.numPattern, self.modelName))
            splitList = self.modelName.split(self.numPattern)
            prefix = splitList[0]
            suffix = splitList[-1]

            # rename object List
            if self.objectsList:
                newNames = numeric_constructor(     prefix          =   prefix,
                                                    suffix          =   suffix,
                                                    decimalPlaces   =   numOcc,
                                                    lenSel          =   len(self.objectsList))
                for i in range(len(self.objectsList)):
                    name=newNames.next()
                    pm.rename(self.objectsList[i], name)

        # string and number pattern
        elif re.search(self.numPattern, self.modelName) and re.search(self.strPattern, self.modelName):
            # occurrences of string pattern
            strOcc = len(re.findall(self.strPattern, self.modelName))

            # occurrences of numeric pattern
            numOcc = len(re.findall(self.numPattern, self.modelName))

            # split the name list: prefix_<str>_middle_<num><num>_mesh
            splitList = [spt
                         for n in self.modelName.split(self.strPattern)
                         for spt in n.split(self.numPattern)
                         if not spt == ""]

            # verify consistency of pattern of names
            if len(splitList) < 3:
                return
            else:
                prefix = splitList[0]
                middle = splitList[1]
                suffix = splitList[-1]

            # instance of alphabetical_constructor
            newAlpNm = alphabetical_constructor  (prefix         = prefix,
                                                  suffix         = middle,
                                                  decimalPlaces  = strOcc,
                                                  lenSel         = int(len(self.objectsList))/self.lPriority)

            # list of names with alphabetical pattern
            baseNames = [newAlpNm.next() for n in range(int(len(self.objectsList))/self.lPriority)]

            # create the final list of names
            allNames = []
            if baseNames:
                for name in baseNames:
                    newNumNm = numeric_constructor(prefix        = name,
                                                   suffix        = suffix,
                                                   decimalPlaces = numOcc,
                                                   lenSel        = self.lPriority)
                    for i in range(self.lPriority):
                        allNames.append(newNumNm.next())

            # rename with new names
            if allNames:
                for index in range(len(allNames)):
                    pm.rename(self.objectsList[index], allNames[index])


def get_selection():
    """
    #
    # # get a list of selected objects (full path name)
    #
    :return: list of long names - pymel instances
    """
    objs = pm.ls(selection=True, long=True)
    if objs:
        return objs


def numeric_constructor(prefix, suffix, decimalPlaces, lenSel):
    """
    #
    # # numeric name generator
    #
    :param prefix: preffix of new name
    :param suffix: suffix of new name
    :param decimalPlaces: amount of decimal places
    :param lenSel: amount of selection list
    :return: new name
    """
    lenSel += 1
    num = 1
    while num < lenSel:
        # yield new name
        yield '{}{:0{}d}{}'.format(prefix, num, decimalPlaces, suffix)
        num +=1


def alphabetical_constructor(prefix, suffix, decimalPlaces=2, lenSel=0):
    """
    #
    # # alphabetical name generator
    #
    :param prefix: preffix of new name
    :param suffix: suffix of new name
    :param decimalPlaces: amount of decimal places
    :param lenSel: amount of selection list
    :return: new name
    """

    # instance of the function letters_constructor
    alphabetSequence = letters_constructor(decimalPlaces)

    num = 0
    while num < lenSel:
        # yield new name
        yield '{}{}{}'.format(prefix, alphabetSequence.next(), suffix)
        num +=1


def letters_constructor(decimalPlaces=2):
    """
    #
    # # generator letter combinations
    #
    :param decimalPlaces: amount of decimal places
    :return: letters combination
    """

    # alphabet list
    alphabet = string.ascii_uppercase

    # generator of letters combination
    letters = ("".join(comb) for comb in cwr(alphabet, decimalPlaces))

    for letter in letters:
        # yield letter sequence
        yield letter
