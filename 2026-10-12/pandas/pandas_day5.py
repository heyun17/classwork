import pandas as pd


# 1. 데이터 불러오기 클래스
class DataLoader:

    def load_csv(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)


# 2. DataLoader를 상속받은 분석 클래스
class DataAnalyzer(DataLoader):

    def __init__(self, file_path: str) -> None:
        self.df = self.load_csv(file_path)

    def get_total_score(self) -> int:
        return int(self.df['score'].sum())

    def get_average_score(self) -> float:
        return float(self.df['score'].mean())


# 3. 객체 생성
analyzer = DataAnalyzer('students.csv')


# 4. 결과 출력
print('=== 전체 학생 데이터 ===')
print(analyzer.df)

print('=== 점수 합계 ===')
print(analyzer.get_total_score())

print('=== 평균 점수 ===')
print(analyzer.get_average_score())