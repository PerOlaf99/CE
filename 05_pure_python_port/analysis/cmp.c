#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define NR_PI 3.141592653589793
#define SWAP(a,b) {double t=(a);(a)=(b);(b)=t;}
void four1(double data[], unsigned long nn, int isign){
  unsigned long n,mmax,m,j,istep,i; double wtemp,wr,wpr,wpi,wi,theta,tempr,tempi;
  n=nn<<1; j=1;
  for(i=1;i<n;i+=2){ if(j>i){ SWAP(data[j],data[i]); SWAP(data[j+1],data[i+1]); }
    m=n>>1; while(m>=2 && j>m){ j-=m; m>>=1; } j+=m; }
  mmax=2;
  while(n>mmax){ istep=mmax<<1; theta=isign*(2.0*NR_PI/mmax);
    wtemp=sin(0.5*theta); wpr=-2.0*wtemp*wtemp; wpi=sin(theta); wr=1.0; wi=0.0;
    for(m=1;m<mmax;m+=2){ for(i=m;i<=n;i+=istep){ j=i+mmax;
        tempr=wr*data[j]-wi*data[j+1]; tempi=wr*data[j+1]+wi*data[j];
        data[j]=data[i]-tempr; data[j+1]=data[i+1]-tempi;
        data[i]+=tempr; data[i+1]+=tempi; }
      wr=(wtemp=wr)*wpr-wi*wpi; wi=wi*wpr+wtemp*wpi+wi; }
    mmax=istep; }
}
int main(void){
  double d[33]; size_t i; unsigned long nn=4;
  for(i=1;i<=2*nn;i++) d[i]=i*1.0;
  four1(d,nn,1);
  printf("NN4 isign=1:\n");
  for(i=1;i<=2*nn;i++) printf("%12.6f\n", d[i]);
  return 0;
}
