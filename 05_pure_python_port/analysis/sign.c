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
      wtemp=wr; wr=wr+wr*wpr-wi*wpi; wi=wi+wi*wpr+wtemp*wpi; }
    mmax=istep; }
}
int main(int argc,char**argv){
  // unitstep again
  double d[17];
  d[1]=1;d[2]=0;d[3]=1;d[4]=0;d[5]=0;d[6]=0;d[7]=0;d[8]=0;
  d[9]=0.5;d[10]=0;d[11]=0.5;d[12]=0;d[13]=0;d[14]=0;d[15]=0;d[16]=0;
  four1(d,8,1);
  printf("ISIGN+1:\n");
  for(int i=1;i<=16;i++) printf("v[%2d]=%11.6f\n", i, d[i]);
  return 0;
}
