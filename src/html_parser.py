from html.parser import HTMLParser
import requests

empty_tags = ["area", "base", "br", "col", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source",
              "track", "wbr"]


class HTMLTree:
    @staticmethod
    def find_first_recursive(tree, tag, attrs):
        if tree["tag"] == tag:
            eq = True
            if attrs is not None:
                s_attrs = tree["attrs"]
                for attr in attrs:
                    try:
                        if s_attrs[attr] != attrs[attr]:
                            eq = False
                            break
                    except KeyError:
                        eq = False
                        break
            if eq:
                return tree
        for sub_tree in tree["children"]:
            result = HTMLTree.find_first_recursive(sub_tree, tag, attrs)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_all_recursive(results, tree, tag, attrs):
        if tree["tag"] == tag:
            eq = True
            if attrs is not None:
                s_attrs = tree["attrs"]
                for attr in attrs:
                    try:
                        if s_attrs[attr] != attrs[attr]:
                            eq = False
                            break
                    except KeyError:
                        eq = False
                        break
            if eq:
                results.append(tree)
        for sub_tree in tree["children"]:
            HTMLTree.find_all_recursive(results, sub_tree, tag, attrs)

    def __init__(self, initial_tree=None):
        if initial_tree is not None:
            self.tree = initial_tree
        else:
            self.tree = {
                "tag": None,
                "data": "",
                "attrs": {},
                "children": []
            }
        self.prev = []
        self.curr = self.tree

    def __str__(self):
        return self.tree.__str__()

    def __repr__(self):
        return self.__str__()

    def add_level(self, name):
        prev = self.curr
        self.prev.append(prev)
        self.curr = {
            "tag": name,
            "data": "",
            "attrs": {},
            "children": []
        }
        prev["children"].append(self.curr)

    def close_level(self):
        if self.prev.__len__() > 0:
            self.curr = self.prev.pop()

    def add_attr(self, name, data):
        self.curr["attrs"][name] = data

    def set_data(self, data):
        self.curr["data"] = self.curr["data"] + data

    def set_decl(self, decl):
        self.tree["tag"] = decl

    def find_first(self, tag, attrs=None):
        tree = HTMLTree.find_first_recursive(self.tree, tag, attrs)
        return HTMLTree(tree)

    def find_all(self, tag, attrs=None):
        trees = []
        HTMLTree.find_all_recursive(trees, self.tree, tag, attrs)
        return list(map(lambda tree: HTMLTree(tree), trees))

    def get_attr(self, name):
        try:
            return self.tree["attrs"][name]
        except KeyError:
            return None

    def get_data(self):
        return self.tree["data"]

    def get_tag(self):
        return self.tree["tag"]

    def get_child(self, index):
        try:
            return self.tree["children"][index]
        except IndexError:
            return None

    def get_children(self):
        return list(map(lambda tree: HTMLTree(tree), self.tree["children"]))


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html_tree = HTMLTree()

    def handle_starttag(self, tag, attrs):
        self.html_tree.add_level(tag)

        for attr in attrs:
            self.html_tree.add_attr(attr[0], attr[1])
        if empty_tags.__contains__(tag):
            self.html_tree.close_level()

    def handle_endtag(self, tag):
        if not empty_tags.__contains__(tag):
            self.html_tree.close_level()

    def handle_data(self, data):
        self.html_tree.set_data(data)

    def handle_comment(self, data):
        pass
        # print("Comment  :", data)

    def handle_decl(self, data):
        self.html_tree.set_decl(data)


# parser = Parser()
#
# html = requests.get("https://abitur.mtuci.ru/ranked_lists/magistracy.php").text
#
# parser.feed(html)
#
# res = parser.html_tree.find_first("div", {"id": "bx_3218110189_4578"}).find_first("a").get_attr("href")
#
# print(res)
