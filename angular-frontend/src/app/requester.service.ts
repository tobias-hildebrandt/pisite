import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http'
import { catchError, map, tap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { Endpoint, PowerStatus, Response } from './models';
import { ENDPOINTS } from './data';

@Injectable({
  providedIn: 'root'
})
export class RequesterService {

  httpOptions = {
    headers: new HttpHeaders({ 'Content-Type': 'application/json' })
  };

  constructor(private http: HttpClient) { }

  private log(message: String) {
    let date: string = new Date().toISOString();
    console.log(`${date}: ${message}`);
  }

  getTest(): Observable<Response<any>> {
    return this.http.get<Response<any>>('/api/test').pipe(
      tap(_ => this.log('fetched test')), 
      catchError(this.handleError<any>('getTest'))
      );
  }

  getEndpoints(): Observable<Response<Endpoint[]>> {
    // return this.http.get<Response<Endpoint[]>>('/api/endpoints').pipe(
    //   tap(_ => this.log('fetched endpoints')), 
    //   catchError(this.handleError<any>('updateEndpoints'))
    //   );
    return of({success: true, message: "", data: ENDPOINTS} );
  }

  getStatus<T extends PowerStatus>(endpoint: Endpoint): Observable<Response<T>> {
    return this.http.get<Response<T>>(endpoint.url).pipe(
      tap(_ => this.log(`fetched status for endpoint: ${endpoint.name}`)),
      catchError(
        this.handleError<Response<T>>(
          `getStatus endpoint:'${endpoint.name}'`, 
          {success: false, message: "unable to fetch status", data: null })
        )
      );
  }

  private handleError<T>(operation = 'operation', failsafe?: T) {
    return (error: any): Observable<T> => {
      console.error(error);
      this.log(`${operation} failed: ${error.message}`);

      return of(failsafe as T);
    }
  }
}
