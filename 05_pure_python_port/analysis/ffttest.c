#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define NR_PI 3.141592653589793
#define SWAP(a,b) {double tempr=(a);(a)=(b);(b)=tempr;}

void four1(double data[], unsigned long nn, int isign) {
    unsigned long n, mmax, m, j, istep, i;
    double wtemp, wr, wpr, wpi, wi, theta;
    double tempr, tempi;
    n = nn << 1;
    j = 1;
    for (i = 1; i < n; i += 2) {
        if (j > i) {
            SWAP(data[j], data[i]);
            SWAP(data[j + 1], data[i + 1]);
        }
        m = n >> 1;
        while (m >= 2 && j > m) {
            j -= m;
            m >>= 1;
        }
        j += m;
    }
    mmax = 2;
    while (n > mmax) {
        istep = mmax << 1;
        theta = isign * (2.0 * NR_PI / mmax);
        wtemp = sin(0.5 * theta);
        wpr = -2.0 * wtemp * wtemp;
        wpi = sin(theta);
        wr = 1.0;
        wi = 0.0;
        for (m = 1; m < mmax; m += 2) {
            for (i = m; i <= n; i += istep) {
                j = i + mmax;
                tempr = wr * data[j] - wi * data[j + 1];
                tempi = wr * data[j + 1] + wi * data[j];
                data[j] = data[i] - tempr;
                data[j + 1] = data[i + 1] - tempi;
                data[i] += tempr;
                data[i + 1] += tempi;
            }
            wr = (wtemp = wr) * wpr - wi * wpi;
            wi = wi * wpr + wtemp * wpi + wi;
        }
        mmax = istep;
    }
}

int main(void) {
    double unitstep[17];
    size_t idx;
    unitstep[1] = 1.0; unitstep[2] = 0.0;
    unitstep[3] = 1.0; unitstep[4] = 0.0;
    unitstep[5] = 0.0; unitstep[6] = 0.0;
    unitstep[7] = 0.0; unitstep[8] = 0.0;
    unitstep[9] = 0.5; unitstep[10] = 0.0;
    unitstep[11] = 0.5; unitstep[12] = 0.0;
    unitstep[13] = 0.0; unitstep[14] = 0.0;
    unitstep[15] = 0.0; unitstep[16] = 0.0;
    four1(unitstep, 8, 1);
    printf("FFT:\n");
    for (idx = 1; idx <= 16; idx++) printf("v[%2lu]=%11.6f\n", idx, unitstep[idx]);
    four1(unitstep, 8, -1);
    printf("IFFT:\n");
    for (idx = 1; idx <= 16; idx++) printf("v[%2lu]=%11.6f\n", idx, unitstep[idx]);
    return 0;
}
