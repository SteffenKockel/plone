def install(self):
        # ....
        # Check that the tool has not been added using its id
        if not hasattr(self, 'webmail_tool'):
            addTool = self.manage_addProduct['WebmailTool'].manage_addTool
            # Add the tool by its meta_type
            addTool('Webmail Tool')