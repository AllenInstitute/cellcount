function [] = FM_script(f1,f2)
%Inputs are indices to files. To process all files,
%set f1 = 1 and f2 = length(im_dir)


im_dir = '/Users/fruity/Dropbox/AllenInstitute/CellCount/dat/raw/control_retraining/';
csv_dir = '/Users/fruity/Dropbox/AllenInstitute/CellCount/dat/raw/control_retraining/';
mat_dir = '/Users/fruity/Dropbox/AllenInstitute/CellCount/dat/proc/control_retraining/';

csvfile = dir([im_dir]);
csvfile = {csvfile.name};
csvfile = {csvfile{contains(csvfile,'-optim.csv')}}';
IM_file = strrep(csvfile,'-optim.csv','.tif');

%Parameters:
FM_max_dist = 40;
gauss_sigma = 2;

%for i = 1:numel(csvfile)
for i = f1:f2
    IM = tifvol2mat([im_dir,IM_file{i}],[],[]);IM=IM(:,:,1);
    r = readmatrix([csv_dir,strrep(csvfile{i},'.tif','.csv')]);
    
    if numel(r)>0
        SVr = [r(:,2),r(:,1),ones(size(r,1))];
        imfilt = imgaussfilt(IM./max(IM(:)),gauss_sigma);
        [S,~,D,T]=FM(imfilt,SVr,FM_max_dist,[1,1,1]);
        
        %{
        figure,imshow(IM,[]);hold on;
        c = contour(T,[10,20,25,30]);
        plot(S(:,2),S(:,1),'.r','MarkerSize',10)
        B1 = bwboundaries(T<=500);
        visboundaries(gca,B1,'Color','c');
        %}
    else
        S = [];
        T = inf(size(IM));
        D = inf(size(IM));
    end
    save([mat_dir,strrep(csvfile{i},'-optim.csv','.mat')],'S','D','T','IM')
    
end