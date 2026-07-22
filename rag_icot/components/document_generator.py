class DocumentGenerator:

    def generate_document(self, row):

        document = f"""
        Source IP: {row['id.orig_h']}
        Destination IP: {row['id.resp_h']}
        Protocol: {row['proto']}
        Label: {row['label']}
        Detailed Label: {row['detailed-label']}
        """

        return document