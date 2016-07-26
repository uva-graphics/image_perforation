#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/opencv.hpp>
#include <string>
using namespace std;
using namespace cv;
#include <Windows.h>

void get_all_files_names_within_folder(string folder,vector<string> &names)
{
	char search_path[200];
	sprintf(search_path, "%s*.*", folder.c_str());
	WIN32_FIND_DATA fd;
	HANDLE hFind = ::FindFirstFile(search_path, &fd);
	if (hFind != INVALID_HANDLE_VALUE) {
		do {
			// read all (real) files in current folder
			// , delete '!' read other 2 default folder . and ..
			if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
				names.push_back(fd.cFileName);
			}
		} while (::FindNextFile(hFind, &fd));
		::FindClose(hFind);
	}
}
int main(int argc, char *argv[]) {
	//argv [0] is program name;argv[1] is train data directory. arg[2] is the output directory. 
	vector<string> names;
	string inputdirectory;
	inputdirectory.append(argv[1]).append("//");
	get_all_files_names_within_folder(inputdirectory, names);
	cout << "read" << names.size() << "files";
	for (int n = 0; n < names.size(); n++)
	{
		Mat img = imread(inputdirectory + names[n], 1);
		Mat src;
		GaussianBlur(img, src, Size(5, 5), 0.95, 0.0, BORDER_CONSTANT);
		Mat dst = Mat::zeros(src.rows, src.cols, CV_8UC1);
		int Max_row = src.rows;
		int Max_col = src.cols;
		for (int r = 0; r < src.rows / 2 + 1; r++)
		{
			for (int c = 0; c < src.cols / 2 + 1; c++)
			{
				if (r * 2 < Max_row&&c * 2 < Max_col)
				{
					dst.at<uchar>(r * 2, c * 2) = (uchar)src.at<Vec3b>(r * 2, c * 2)[2]; //red
				}
				if (r * 2 < Max_row&&c * 2 + 1< Max_col)
				{
					dst.at<uchar>(r * 2, c * 2 + 1) = (uchar)src.at<Vec3b>(r * 2, c * 2 + 1)[1];//green
				}
				if (r * 2 + 1< Max_row&&c * 2 < Max_col)
				{
					dst.at<uchar>(r * 2 + 1, c * 2) = (uchar)src.at<Vec3b>(r * 2 + 1, c * 2)[1];//green
				}
				if (r * 2 + 1< Max_row&&c * 2 + 1< Max_col)
				{
					dst.at<uchar>(r * 2 + 1, c * 2 + 1) = (uchar)src.at<Vec3b>(r * 2 + 1, c * 2 + 1)[0];//red	
				}
			}
		}
		
		string output_path;
		output_path.append(argv[2]).append("//").append(names[n]);
		imwrite(output_path, dst);
	}
	
	return 0;
}