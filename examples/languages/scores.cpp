#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// 성공하면 true, 입력이 끝났으면 false를 반환합니다.
bool readScore(int index, int& result) {
    std::string line;
    while (true) {
        std::cout << "Score " << index << ": ";
        if (!std::getline(std::cin, line)) {
            return false;
        }
        std::istringstream input(line);
        int value = 0;
        char extra = '\0';
        if (!(input >> value) || (input >> extra)
                || value < 0 || value > 100) {
            std::cout << "Enter an integer from 0 to 100.\n";
            continue;
        }
        result = value;
        return true;
    }
}

int main() {
    std::vector<int> scores;
    for (int index = 1; index <= 3; ++index) {
        int score = 0;
        if (!readScore(index, score)) {
            std::cerr << "Input ended before all scores were entered.\n";
            return 1;
        }
        scores.push_back(score);
    }
    int total = 0;
    int passed = 0;
    for (int score : scores) {
        total += score;
        if (score >= 60) {
            ++passed;
        }
    }
    double average = static_cast<double>(total) / scores.size();
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Average: " << average << '\n';
    std::cout << "Passed: " << passed << '\n';
}
