import { TestOutput } from "reproduction-learning-engine-frontend";

// Hasil eksekusi hidden test. Kegagalan DITAMPILKAN (cermin §7.6), bukan disembunyikan.
export function Pass() {
  return (
    <div style={{ maxWidth: 620 }}>
      <TestOutput passed output={"collected 3 items\n\ntest_paginate.py ...              [100%]\n\n3 passed in 0.12s"} />
    </div>
  );
}

export function Fail() {
  return (
    <div style={{ maxWidth: 620 }}>
      <TestOutput
        passed={false}
        output={
          "test_path_param_404.py F                       [100%]\n\n" +
          "E   assert response.status_code == 404\n" +
          "E    +  where 200 = <Response [200]>.status_code\n\n" +
          "1 failed in 0.09s"
        }
      />
    </div>
  );
}

export function TimedOut() {
  return (
    <div style={{ maxWidth: 620 }}>
      <TestOutput passed={false} timedOut output={"(eksekusi melebihi 10 detik — dihentikan)"} />
    </div>
  );
}
