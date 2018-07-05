#####################################################



#####################################################

#####################################################
#                   READ IN DATA                    #
#####################################################
import pandas as pd

def read_csv(direct, fname, time_column, **kwargs):

    """
    Reads in data from a single file assuming it
    is a collection of time series. Returns df.
    """

    data = pd.read_csv(direct+fname, index_col=time_column, parse_dates=True)
    return data


def merge_files(list_of_files, file_out_name):

    """
    Provided with a list of identically formatted files,
    this method will merge all files into a single file
    whose name is user specified. The header is read from
    the first file in the list_of_files and ignored from then on.
    """

    list_of_files = sorted(list_of_files)
    f_out = open(file_out_name,"a")

    for line in open(list_of_files[0]):
        line = ','.join(line.split())+"\n"
        f_out.write(line)

    for f in list_of_files[1:]:
        f_open = open(f)
        f_open.next()

        for line in f_open:
            line = ','.join(line.split())+"\n"
            f_out.write(line)
        f_open.close()

    f_out.close()
