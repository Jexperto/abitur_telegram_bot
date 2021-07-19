import pandas as pd


class ApplicantsData():

    """
    Class for extractiong application data for certain specialty
    :param df: Pandas dataframe that is already filtered by specialty, budget and full time education form
    :param specialty: The specialty by which the dataframe was filtered
    """

    def __init__(self, file, specialty):
        '''

        :param filename: path to a .xls file
        :param specialty: the specialty by which to filter the table
        '''
        self.df = pd.read_excel(file)
        self.specialty = specialty
        self.df = self.df[self.df["Направление (специальность)"] == self.specialty]
        self.df = self.df[self.df["Основание поступления"] == "Бюджетная основа"]
        self.df = self.df[self.df["Форма обучения"] == "Очная"]

    def amount(self, consent=False):
        '''

        :param consent: if True returns only info about applicants who submitted consent to admission
        :return: amount of applicants on specialty
        '''
        if consent:
            return len(self.df[self.df["Согласие на зачисление"] == "Да"])
        return len(self.df)

    def point_summary(self, consent=False, binsBy=10, sort=False, ascending=False):
        '''
        :param consent: if True returns only info about applicants who submitted consent to admission
        :param binsBy: tells how to split the table for better representation (for example the value of 10 means it will
        be grouped in bins such as (0..10],(10..20],(20..30]...]
        :param sort: whether to sort at all
        :param ascending: whether to sort in ascending order
        :return: amount of people by points ranges
        '''
        if consent:
            temp = self.df[self.df["Согласие на зачисление"] == "Да"]
            return temp["Сумма баллов"].value_counts(bins=[i * 10 for i in range(binsBy + 1)],sort=sort,ascending=ascending)
        return self.df["Сумма баллов"].value_counts(bins=[i * 10 for i in range(binsBy + 1)],sort=sort,ascending=ascending)

    def amount_applicants_higher_than(self, value, consent=False):
        '''
        :param value: points by which filter
        :param consent: if True returns only info about applicants who submitted consent to admission
        :return: amount of applicants who have higher points value than given
        '''
        if consent:
            temp = self.df[self.df["Согласие на зачисление"] == "Да"]
            return len(temp[self.df["Сумма баллов"] > value])
        return len(self.df[self.df["Сумма баллов"] > value])


# test
if __name__ == "__main__":
    a = ApplicantsData("../../abitur_bot/table.xls", "09.04.01 Информатика и вычислительная техника")
    # print(a.amount_applicants_higher_than(10,consent=False))
    print(a.amount())
