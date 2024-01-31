import wx
import wx.lib.dialogs
import json

"""
THINGS TO ADD:
Source, target, and direction labels on the UI to show what is currently selected

Previous relation for current sentence should be visible to user to indicate the program
is working properly and so it is easier for researchers to know/remember what they have already labeled

Currently cannot add metadata (author, title, year) in UI
    Could maybe add metadata options to "load paper" element and have it assign to all sentences entered
    Solution is probably coming by allowing for an input text file (pdf, rtf, etc) and reading in the metadata then

PDF,RTF, whatever other text format reader and parser needs to be added
    Prompts for file upon opening (?)
    
When adding sentences, currently only works with periods
    Adding functionality to other things that end a sentence would be nice (?,!)
    
Currently saves the json file only, maybe create way to save current state in case someone can't finish a paper immediately. -Kinda stretch

On launch ask for a paper - for final version

Need to refactor how the relations are saved
    New structure should probably be:
        Read in paper->create new relation object with text and metadata
        Save new relation objects into list (at this point its basically JSON output format)
        Now UI elements come into play:
            Loop through list of relation objects
            UI shows sentence by sentence and allows for data labeling
            **since every sentence is now an object, saving becomes much easier and simpler
            **may have some weird saving edge cases

Current Functionality:
Can add new sentences (papers) from the file menu
Closes when out of sentences, opens and asks for more sentences before closing
No matter how it closes, it creates a json file from labeled_sentences.
Both source and target are required for a valid labeled sentence, direction is not. (currently)

"""

class relations:
    """
    This class is used to store the relations and create
    the dictionary sections of the json file
    """

    def __init__(self, inp):
        self.text = inp

        self.title, self.authors = "", ""
        self.year = -1
        self.outer_dict = {"text": self.text,
                           "casual relations": [],
                           "meta_data": {"title": self.title, "authors": self.authors, "year": self.year}}

    def source(self, inp):
        if inp == None:
            return self.outer_dict["casual relations"][0]["src"]
        self.outer_dict["casual relations"][0]["src"] = inp

    def target(self, inp):
        if inp == None:
            return self.outer_dict["casual relations"][0]["tgt"]
        self.outer_dict["casual relations"][0]["tgt"] = inp

    def direction(self, inp):
        if inp == None:
            return self.outer_dict["casual relations"][0]["direction"]
        self.outer_dict["casual relations"][0]["direction"] = inp

    def casual_relations(self, inp):
        """
        This function takes the a casual relation in format [src,tgt,direction] and adds it to the current relation
        :param inp: list of strings
        :return: none
        """
        temp_relation = {"src": inp[0], "tgt": inp[1], "direction": inp[2]}
        self.outer_dict["casual relations"].append(temp_relation)


class TextEditor(wx.Frame):
    def __init__(self, *args, **kw):
        super(TextEditor, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.sentences = [
            "The wind farms in the Gulf of Mexico create new fishing zones.",
            "Other perceived impacts of the BIWF included the negative effects of sound and increased turbidity during construction and an increase in cod in the area.",
            "The curious cat explored the mysterious backyard at night."
        ]
        self.labeled_sentences = []
        self.relation = relations("")
        self.current_sentence_index = 0
        self.default_sentence = self.sentences[self.current_sentence_index]

        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, value=self.default_sentence)
        self.text_ctrl.Bind(wx.EVT_LEFT_UP, self.on_select)

        self.source = None
        self.target = None
        self.direction = None

        self.filename = None
        self.create_menu()
        self.create_file_menu()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(wx.Button(self.panel, label="Increase", id=wx.ID_ANY, size=(80, -1)), 0, wx.ALL, 5)
        button_sizer.Add(wx.Button(self.panel, label="Decrease", id=wx.ID_ANY, size=(80, -1)), 0, wx.ALL, 5)
        button_sizer.Add(wx.Button(self.panel, label="Save Relation", id=wx.ID_ANY, size=(80, -1)), 0, wx.ALL, 5)
        button_sizer.Add(wx.Button(self.panel, label="Reset", id=wx.ID_ANY, size=(80, -1)), 0, wx.ALL, 5)
        button_sizer.Add(wx.Button(self.panel, label="Next", id=wx.ID_ANY, size=(80, -1)), 0, wx.ALL, 5)

        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT)

        self.panel.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.on_button_click, id=wx.ID_ANY)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def create_menu(self):
        self.menu = wx.Menu()
        self.menu.Append(wx.ID_ANY, "Source", "Set as Source")
        self.menu.Append(wx.ID_ANY, "Target", "Set as Target")
        self.menu.Append(wx.ID_ANY, "Cancel", "Cancel selection")

        self.Bind(wx.EVT_MENU, self.on_menu_item, id=wx.ID_ANY)

    def create_file_menu(self):
        file_menu = wx.Menu()
        self.paper_load = wx.NewIdRef(count=1)
        file_menu.Append(wx.ID_OPEN, "&Open", "Open a file")
        file_menu.Append(wx.ID_SAVE, "&Save", "Save the current file")
        file_menu.Append(wx.ID_SAVEAS, "Save &As", "Save the current file with a new name")
        file_menu.Append(self.paper_load, "Load &Paper", "Load more sentences")

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_save_as, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_load_paper, id=self.paper_load)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

    def on_open(self, event):
        wildcard = "JSON files (*.json)|*.json"
        dialog = wx.FileDialog(self, "Open File", wildcard=wildcard, style=wx.FD_OPEN)

        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            with open(filename, 'r') as file:
                content = file.read()
                self.text_ctrl.SetValue(content)

        dialog.Destroy()
    def override_save(self):
        #The function below is an edge case of inputting a src, tgt, and direction, then closing without hitting "Save Relation"
        if self.relation.text != "":  # unused sentence is equivilent to blank string
            self.save_relation()
            # Edge case of the inner edge case: If nothing is in labeled sentences, we just add the relation
            if len(self.labeled_sentences):
                # Edge case: if you hit save after min 1 save on a sentence, but then add another relation from the same sentence
                # and save again, we override from our labeled sentences, as to not duplicate the text and all its relations
                if self.labeled_sentences[-1]["text"] == self.default_sentence:
                    self.labeled_sentences[-1] = self.relation.outer_dict
                else:
                    self.labeled_sentences.append(self.relation.outer_dict)
            else:
                self.labeled_sentences.append(self.relation.outer_dict)
    def on_save(self, event):
        # The if below is an edge case of inputting a src, tgt, and direction, then closing without hitting "Save Relation"

        if self.filename is None:
            self.on_save_as(wx.ID_SAVEAS)
        else:
            self.override_save()
            with open(self.filename, "w") as f:
                json.dump(self.labeled_sentences, f)

    def on_save_as(self, event):
        self.override_save()
        wildcard = "JSON files (*.json)|*.json"
        dialog = wx.FileDialog(self, "Save As", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dialog.ShowModal() == wx.ID_OK:
            self.filename = dialog.GetPath()
            with open(self.filename, "w") as f:
                json.dump(self.labeled_sentences, f)

        dialog.Destroy()

    def on_load_paper(self, event):
        with wx.TextEntryDialog(self, "Enter more sentences (separated by a period)", "Load Paper") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                additional_sentences = dlg.GetValue().split('.')
                self.sentences.extend([sentence.strip() for sentence in additional_sentences if sentence.strip()])
                print("Loaded additional sentences:", additional_sentences)

    def on_exit(self, event):
        self.Close()

    def on_select(self, event):
        pos = event.GetPosition()
        start, end = self.text_ctrl.GetSelection()

        if start != end:
            self.show_menu(pos)

        event.Skip()

    def show_menu(self, pos):
        self.PopupMenu(self.menu, pos)

    def on_menu_item(self, event):
        """

        :param event:
        :return:
        """
        label = self.menu.GetLabel(event.GetId())

        if label == "Source":
            self.source = self.get_selected_words()
        elif label == "Target":
            self.target = self.get_selected_words()
        elif label == "Cancel":
            pass

    def on_button_click(self, event):
        """

        :param event:
        :return:
        """
        button_label = event.GetEventObject().GetLabel()

        if button_label == "Increase" or button_label == "Decrease":
            self.direction = button_label
        elif button_label == "Reset":
            self.reset_selection()
        elif button_label == "Save Relation":
            self.save_relation()
            self.reset_selection()
        elif button_label == "Next":
            self.save_and_next()

    def get_selected_words(self):
        start, end = self.text_ctrl.GetSelection()
        return self.text_ctrl.GetValue()[start:end]

    def reset_selection(self):
        """

        :return:
        """
        print(f"Source: {self.source}, Target: {self.target}, Direction: {self.direction}")
        self.source = None
        self.target = None
        self.direction = None
        self.text_ctrl.SetSelection(-1, -1)

    def save_relation(self):
        # Could add direction below, but what if we know there's a connection but don't know the direction?
        if all(element is not None for element in [self.source, self.target]):
            if self.relation.text == self.default_sentence:
                self.relation.casual_relations([self.source, self.target, self.direction])
            else:
                self.relation = relations(self.default_sentence)
                self.relation.casual_relations([self.source, self.target, self.direction])
            print("Saving:", f"Source: {self.source}, Target: {self.target}, Direction: {self.direction}")

    def save_and_next(self):
        """


        :return:
        """

        self.save_relation()
        if self.relation.text != "":  # unused sentence is equivilent to blank string
            self.labeled_sentences.append(self.relation.outer_dict)
        self.relation = relations("")
        print("Saving:", f"Source: {self.source}, Target: {self.target}, Direction: {self.direction}")
        self.current_sentence_index += 1

        if self.current_sentence_index < len(self.sentences):
            self.text_ctrl.SetValue(self.sentences[self.current_sentence_index])
            self.reset_selection()
        else:
            print("No more sentences.")
            self.on_load_paper(event=self.paper_load)
            if self.current_sentence_index < len(self.sentences):
                self.text_ctrl.SetValue(self.sentences[self.current_sentence_index])
                self.reset_selection()
            elif len(self.labeled_sentences) > 0:
                self.on_save(wx.ID_SAVE)
                self.Destroy()
            else:
                self.Destroy()

    def on_close(self, event):
        if len(self.labeled_sentences) > 0:
            self.on_save(wx.ID_SAVE)
            self.Destroy()
        elif self.relation.text != "":
            self.on_save(wx.ID_SAVE)
            self.Destroy()
        else:
            self.Destroy()


if __name__ == "__main__":
    app = wx.App(False)
    frame = TextEditor(None, title="Text Editor", size=(800, 600))
    frame.Show()
    app.MainLoop()
